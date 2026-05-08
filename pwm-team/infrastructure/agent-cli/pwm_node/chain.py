"""Contract call wrappers over web3.py.

Provides ``PWMChain`` — one class that owns a web3 connection, loads the 7
contract ABIs from ``interfaces/contracts_abi/``, resolves addresses from
``interfaces/addresses.json`` for the selected network, and exposes the
read/write methods pwm-node commands need.

Design:
- Read methods never require a wallet; callable even with ``PWM_PRIVATE_KEY``
  unset.
- Write methods require ``PWM_PRIVATE_KEY`` env var (Phase C session 2) —
  OS-keychain integration deferred to a later session (see bounty spec §3).
- Wraps failures in ``ChainError`` with actionable messages.
- Pure functions where possible; state is only in the ``PWMChain`` instance.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, Web3RPCError
    from eth_account import Account
    _WEB3_AVAILABLE = True
except ImportError:
    _WEB3_AVAILABLE = False


# The 7 PWM contracts — one ABI file per name, matched in addresses.json
CONTRACT_NAMES = (
    "PWMRegistry",
    "PWMMinting",
    "PWMStaking",
    "PWMCertificate",
    "PWMReward",
    "PWMTreasury",
    "PWMGovernance",
)


# Default RPC endpoints per network. Lookup key is `net_info["network"]`
# from addresses.json (testnet→"sepolia", mainnet→"base"). Override via
# PWM_RPC_URL env var. Note: PWM's mainnet target is Base (chainId 8453),
# NOT Ethereum mainnet — see addresses.json:mainnet for the canonical
# chainId. The legacy "mainnet" key is preserved as an alias for "base"
# for callers that pass network="mainnet" without consulting addresses.json.
DEFAULT_RPCS = {
    "sepolia": "https://rpc.sepolia.org",
    "base": "https://mainnet.base.org",
    "mainnet": "https://mainnet.base.org",
}


class ChainError(RuntimeError):
    """Actionable failure from a chain interaction."""


@dataclass
class ContractRef:
    """A loaded, connected contract — address + ABI + web3 contract object."""
    name: str
    address: str
    abi: list
    contract: Any  # web3.contract.Contract


def _interfaces_dir(start: Path | None = None) -> Path:
    """Walk up from ``start`` (or cwd) looking for an interfaces dir.

    Probes two candidate locations in order:

      1. ``pwm-team/infrastructure/agent-contracts/`` — mirror-included
         (ships in pwm-public). Holds the canonical ``addresses.json``
         (deploy-script-updated) and ``contracts_abi/*.json``.
      2. ``pwm-team/coordination/agent-coord/interfaces/`` — internal coord
         path (NOT in pwm-public mirror; source-tree only). Legacy fallback
         used by founder workflows pre-migration.

    The mirror path is checked first so external pwm-public consumers get
    a working CLI by default. ``PWM_INTERFACES_DIR`` env var overrides both.

    Required contents at the chosen path: ``addresses.json`` (file) and
    ``contracts_abi/`` (dir with one ``<ContractName>.json`` per contract).
    """
    env_override = os.environ.get("PWM_INTERFACES_DIR")
    if env_override:
        p = Path(env_override).resolve()
        if p.is_dir():
            return p
        raise ChainError(f"PWM_INTERFACES_DIR={env_override} is not a directory")

    cur = (start or Path.cwd()).resolve()
    candidates = (
        ("pwm-team", "infrastructure", "agent-contracts"),
        ("pwm-team", "coordination", "agent-coord", "interfaces"),
    )
    for p in [cur, *cur.parents]:
        for parts in candidates:
            probe = p.joinpath(*parts)
            if (probe / "addresses.json").is_file() and (probe / "contracts_abi").is_dir():
                return probe
    raise ChainError(
        "Cannot find a pwm-team interfaces dir (with addresses.json + contracts_abi/) "
        f"by walking up from {cur}. Tried pwm-team/infrastructure/agent-contracts/ "
        "and pwm-team/coordination/agent-coord/interfaces/. Pass interfaces_dir= to "
        "PWMChain explicitly or set PWM_INTERFACES_DIR."
    )


class PWMChain:
    """Connected PWM chain session. Instantiate once per command invocation.

    Parameters
    ----------
    network: 'testnet' (Sepolia) or 'mainnet'.
    rpc_url: optional RPC override. Defaults to DEFAULT_RPCS[network] or env
             PWM_RPC_URL.
    interfaces_dir: path to pwm-team/coordination/agent-coord/interfaces/
                    (auto-detected from cwd if not passed).
    """

    def __init__(
        self,
        network: str = "testnet",
        rpc_url: str | None = None,
        interfaces_dir: Path | None = None,
    ):
        if not _WEB3_AVAILABLE:
            raise ChainError(
                "web3.py not installed. Run: pip install 'pwm-node'  "
                "(which pulls in web3>=6.0)"
            )
        if network not in ("testnet", "mainnet"):
            raise ChainError(f"network must be 'testnet' or 'mainnet', got: {network!r}")

        self.network = network
        self.interfaces_dir = interfaces_dir or _interfaces_dir()

        # Load addresses for this network
        addresses_file = self.interfaces_dir / "addresses.json"
        try:
            all_addresses = json.loads(addresses_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise ChainError(f"Cannot read addresses.json: {e}")

        network_key = "testnet" if network == "testnet" else "mainnet"
        net_info = all_addresses.get(network_key, {})
        if network == "mainnet" and not net_info.get("PWMRegistry"):
            raise ChainError(
                "Mainnet contracts not yet deployed (addresses.json has null). "
                "Use --network testnet for now."
            )

        self.chain_id = net_info.get("chainId")
        self.addresses = {name: net_info.get(name) for name in CONTRACT_NAMES}
        missing = [n for n, a in self.addresses.items() if not a]
        if missing:
            raise ChainError(
                f"addresses.json[{network_key}] missing contracts: {missing}"
            )

        # Connect to RPC
        resolved_rpc = rpc_url or os.environ.get("PWM_RPC_URL") or DEFAULT_RPCS.get(
            net_info.get("network") or ("sepolia" if network == "testnet" else "mainnet")
        )
        if not resolved_rpc:
            raise ChainError("No RPC URL. Set PWM_RPC_URL or pass rpc_url=")
        self.w3 = Web3(Web3.HTTPProvider(resolved_rpc, request_kwargs={"timeout": 20}))
        if not self.w3.is_connected():
            raise ChainError(f"Cannot connect to RPC {resolved_rpc}")

        # Load ABIs, build contract objects
        self.contracts: dict[str, ContractRef] = {}
        for name in CONTRACT_NAMES:
            abi_path = self.interfaces_dir / "contracts_abi" / f"{name}.json"
            try:
                abi_raw = json.loads(abi_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                raise ChainError(f"Cannot read ABI for {name}: {e}")
            # ABI files may store the ABI directly (list) or under an 'abi' key (hardhat style)
            abi = abi_raw if isinstance(abi_raw, list) else abi_raw.get("abi", [])
            addr_cs = self.w3.to_checksum_address(self.addresses[name])
            contract = self.w3.eth.contract(address=addr_cs, abi=abi)
            self.contracts[name] = ContractRef(
                name=name, address=addr_cs, abi=abi, contract=contract
            )

    # ───── wallet handling ─────

    def _get_account(self):
        """Resolve a signer account from PWM_PRIVATE_KEY env var.

        OS-keychain integration deferred to a later session per CLAUDE.md §3.
        """
        pk = os.environ.get("PWM_PRIVATE_KEY")
        if not pk:
            raise ChainError(
                "PWM_PRIVATE_KEY env var not set. Required for write operations. "
                "Set via: export PWM_PRIVATE_KEY=0x<your-64-char-hex>"
            )
        if not pk.startswith("0x"):
            pk = "0x" + pk
        try:
            return Account.from_key(pk)
        except Exception as e:
            raise ChainError(f"Invalid private key format: {e}")

    def signer_address(self) -> str | None:
        """Return the signer address if a key is configured, else None.

        Never raises — used for `balance` and UX prompts.
        """
        try:
            return self._get_account().address
        except ChainError:
            return None

    # ───── read methods (no wallet required) ─────

    def get_balance(self, address: str | None = None) -> float:
        """Return native ETH balance in ether. Uses signer address if none given."""
        addr = address or self.signer_address()
        if not addr:
            raise ChainError("No address provided and no PWM_PRIVATE_KEY signer configured")
        wei = self.w3.eth.get_balance(self.w3.to_checksum_address(addr))
        return float(self.w3.from_wei(wei, "ether"))

    def get_artifact(self, artifact_hash: str) -> dict | None:
        """Look up an artifact by its 32-byte hash in PWMRegistry.

        Returns the decoded artifact struct as a dict, or None if not registered.
        """
        reg = self.contracts["PWMRegistry"].contract
        h = artifact_hash if artifact_hash.startswith("0x") else "0x" + artifact_hash
        try:
            # Method name may be getArtifact / artifacts — depends on the ABI.
            # Probe for the most likely read functions.
            if hasattr(reg.functions, "getArtifact"):
                raw = reg.functions.getArtifact(h).call()
            elif hasattr(reg.functions, "artifacts"):
                raw = reg.functions.artifacts(h).call()
            else:
                raise ChainError(
                    "PWMRegistry has no getArtifact() or artifacts() function. "
                    "Check ABI at interfaces/contracts_abi/PWMRegistry.json"
                )
        except (ContractLogicError, Web3RPCError) as e:
            # Not-found typically reverts — return None rather than raise
            if "revert" in str(e).lower() or "invalid" in str(e).lower():
                return None
            raise ChainError(f"getArtifact({h}) failed: {e}")
        # Decode tuple-return into a dict using ABI output names when available
        return {"raw": raw, "hash": h}

    def get_pool_balance(self, principle_hash: str, spec_hash: str, bench_hash: str) -> int:
        """Return the current draw-pool balance for one (k,j,b) benchmark key, in wei."""
        reg = self.contracts["PWMReward"].contract
        for h in (principle_hash, spec_hash, bench_hash):
            if not h.startswith("0x"):
                h = "0x" + h
        try:
            if hasattr(reg.functions, "poolBalance"):
                return int(reg.functions.poolBalance(principle_hash, spec_hash, bench_hash).call())
            return 0
        except (ContractLogicError, Web3RPCError) as e:
            raise ChainError(f"poolBalance({principle_hash}, {spec_hash}, {bench_hash}) failed: {e}")

    def block_number(self) -> int:
        """Latest block number on the target chain."""
        return int(self.w3.eth.block_number)

    # ───── write methods (wallet required) ─────

    # 12-field SubmitArgs struct order — must match
    # interfaces/contracts_abi/PWMCertificate.json.
    _SUBMIT_STRUCT_FIELDS = (
        "certHash",
        "benchmarkHash",
        "principleId",
        "l1Creator",
        "l2Creator",
        "l3Creator",
        "acWallet",
        "cpWallet",
        "shareRatioP",
        "Q_int",
        "delta",
        "rank",
    )

    def _build_submit_tuple(self, cert_payload: dict) -> tuple:
        """Convert the JSON cert payload into the ABI-encodable 12-tuple.

        Converts bytes32 hex strings to raw bytes (web3.py 7.x requires this),
        checksums the five address fields, and casts integers.
        """
        missing = [k for k in self._SUBMIT_STRUCT_FIELDS if k not in cert_payload]
        if missing:
            raise ChainError(
                f"cert_payload missing struct fields: {missing}. "
                "Rebuild with `pwm-node mine` or check interfaces/cert_schema.json."
            )

        def _to_bytes32(hex_str: str) -> bytes:
            if not isinstance(hex_str, str):
                raise ChainError(f"expected bytes32 hex str, got {type(hex_str).__name__}")
            h = hex_str[2:] if hex_str.startswith("0x") else hex_str
            if len(h) != 64:
                raise ChainError(f"bytes32 hex must be 64 chars, got {len(h)}")
            return bytes.fromhex(h)

        return (
            _to_bytes32(cert_payload["certHash"]),
            _to_bytes32(cert_payload["benchmarkHash"]),
            int(cert_payload["principleId"]),
            self.w3.to_checksum_address(cert_payload["l1Creator"]),
            self.w3.to_checksum_address(cert_payload["l2Creator"]),
            self.w3.to_checksum_address(cert_payload["l3Creator"]),
            self.w3.to_checksum_address(cert_payload["acWallet"]),
            self.w3.to_checksum_address(cert_payload["cpWallet"]),
            int(cert_payload["shareRatioP"]),
            int(cert_payload["Q_int"]),
            int(cert_payload["delta"]),
            int(cert_payload["rank"]),
        )

    def submit_certificate(self, cert_payload: dict, *, gas: int = 500000) -> str:
        """Call PWMCertificate.submit(SubmitArgs). Returns tx hash (hex string).

        ``cert_payload`` must match the 12-field schema in
        ``interfaces/cert_schema.json``. Any ``_meta`` block is ignored.
        """
        acct = self._get_account()
        cert = self.contracts["PWMCertificate"].contract

        if not hasattr(cert.functions, "submit"):
            raise ChainError(
                "PWMCertificate has no submit() function. "
                "Check ABI at interfaces/contracts_abi/PWMCertificate.json"
            )

        struct = self._build_submit_tuple(cert_payload)
        fn = cert.functions.submit(struct)

        try:
            gas = fn.estimate_gas({"from": acct.address})
        except Exception as e:
            # Most reverts surface here; propagate with actionable context.
            raise ChainError(
                f"gas estimation failed (likely on-chain revert): {e}. "
                "Is benchmarkHash registered to PWMRegistry and is the wallet funded?"
            )

        tx = fn.build_transaction(
            {
                "from": acct.address,
                "chainId": self.chain_id,
                "nonce": self.w3.eth.get_transaction_count(acct.address),
                "gas": int(gas * 1.2),
                "maxFeePerGas": max(self.w3.eth.gas_price * 2, self.w3.to_wei(2, "gwei")),
                "maxPriorityFeePerGas": self.w3.to_wei(1, "gwei"),
            }
        )
        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction  # type: ignore[attr-defined]
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        tx_hex = tx_hash.hex() if isinstance(tx_hash, bytes) else str(tx_hash)
        return tx_hex if tx_hex.startswith("0x") else "0x" + tx_hex

    def wait_for_tx(self, tx_hash: str, *, timeout_s: int = 300) -> dict:
        """Block until ``tx_hash`` is mined. Returns the receipt as a dict.

        Raises ChainError on timeout or tx failure.
        """
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout_s)
        except Exception as e:
            raise ChainError(f"wait_for_tx({tx_hash}) failed: {e}")
        if receipt.get("status") == 0:
            raise ChainError(f"Transaction {tx_hash} reverted on-chain")
        return dict(receipt)

    # ───── staking ─────

    # Layer constants per PWMStaking ABI (match the on-chain LAYER_* view returns)
    LAYER_PRINCIPLE = 0
    LAYER_SPEC = 1
    LAYER_BENCHMARK = 2

    _LAYER_NAMES = {0: "principle", 1: "spec", 2: "benchmark"}

    def stake_amount(self, layer: int) -> int:
        """Return the required stake in wei for a given layer (0/1/2)."""
        if layer not in self._LAYER_NAMES:
            raise ChainError(f"layer must be 0, 1, or 2 (got {layer}). See PWMChain.LAYER_*.")
        staking = self.contracts["PWMStaking"].contract
        try:
            return int(staking.functions.stakeAmount(layer).call())
        except (ContractLogicError, Web3RPCError) as e:
            raise ChainError(f"stakeAmount({layer}) failed: {e}")

    def stake_of(self, artifact_hash: str) -> int:
        """Return the current stake on an artifact, in wei."""
        staking = self.contracts["PWMStaking"].contract
        h = artifact_hash if artifact_hash.startswith("0x") else "0x" + artifact_hash
        try:
            # Some ABIs expose stakeOf(bytes32), others stakes(bytes32). Probe.
            if hasattr(staking.functions, "stakeOf"):
                return int(staking.functions.stakeOf(h).call())
            return int(staking.functions.stakes(h).call())
        except (ContractLogicError, Web3RPCError) as e:
            raise ChainError(f"stakeOf({h}) failed: {e}")

    def stake(self, layer: int, artifact_hash: str, *, gas: int = 200000) -> str:
        """Stake on an artifact. Sends the required stake amount as tx value.

        Returns the tx hash. Caller should `wait_for_tx` to confirm.
        """
        if layer not in self._LAYER_NAMES:
            raise ChainError(f"layer must be 0/1/2 (got {layer})")
        acct = self._get_account()
        staking = self.contracts["PWMStaking"].contract
        h = artifact_hash if artifact_hash.startswith("0x") else "0x" + artifact_hash

        required = self.stake_amount(layer)
        if required == 0:
            raise ChainError(
                f"stakeAmount for layer {layer} ({self._LAYER_NAMES[layer]}) is 0 — "
                "has the contract been initialized?"
            )

        fn = staking.functions.stake(layer, h)
        tx = fn.build_transaction(
            {
                "from": acct.address,
                "chainId": self.chain_id,
                "nonce": self.w3.eth.get_transaction_count(acct.address),
                "gas": gas,
                "value": required,
                "maxFeePerGas": max(self.w3.eth.gas_price * 2, self.w3.to_wei(2, "gwei")),
                "maxPriorityFeePerGas": self.w3.to_wei(1, "gwei"),
            }
        )
        signed = acct.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction  # type: ignore[attr-defined]
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        return tx_hash.hex()

    # ───── debug helpers ─────

    def info(self) -> dict:
        """Summary of the chain connection — useful for `pwm-node balance` header."""
        return {
            "network": self.network,
            "chain_id": self.chain_id,
            "block": self.block_number(),
            "signer": self.signer_address(),
            "contracts": {name: ref.address for name, ref in self.contracts.items()},
        }
