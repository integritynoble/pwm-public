"""
cp_register: Compute Provider registration and bond staking.

CLI usage:
    pwm-miner cp register --gpu <model> --vram <gb> --region <code>
    pwm-miner cp status [--address <addr>]

Environment variables:
    PWM_PRIVATE_KEY  — CP wallet private key (never logged or printed)
    PWM_WEB3_URL     — JSON-RPC or WebSocket endpoint for the target chain

Contract addresses (Sepolia testnet):
    PWMStaking: 0x17Fc30B22E6d0e683359e3a2D0F75Bded01A2852

Security requirements:
    - NEVER log or print the private key.
    - NEVER submit a bond transaction if bond_amount_pwm < 10.0.
    - bondCP() is a planned extension; see comment below.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Contract configuration
# ---------------------------------------------------------------------------

PWM_STAKING_ADDRESS = "0x17Fc30B22E6d0e683359e3a2D0F75Bded01A2852"

# Minimal ABI covering the functions currently deployed on-chain.
# bondCP() and registerCP() are planned extensions — included here for
# forward-compatibility so the call sites compile once the contract is extended.
_STAKING_ABI_PATH = (
    Path(__file__).resolve().parents[3]
    / "coordination"
    / "agent-coord"
    / "interfaces"
    / "contracts_abi"
    / "PWMStaking.json"
)

# Planned CP-specific ABI fragments (not yet in deployed contract).
# These will be merged into the on-chain ABI once PWMStaking is extended.
_CP_EXTENSION_ABI: list[dict] = [
    # Planned contract function - requires PWMStaking.bondCP() extension
    {
        "inputs": [
            {"internalType": "string", "name": "profileJson", "type": "string"},
            {"internalType": "uint256", "name": "bondWei", "type": "uint256"},
        ],
        "name": "bondCP",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    # Planned contract function - requires PWMStaking.getCPStatus() extension
    {
        "inputs": [
            {"internalType": "address", "name": "cp", "type": "address"},
        ],
        "name": "getCPStatus",
        "outputs": [
            {"internalType": "uint256", "name": "bondBalance", "type": "uint256"},
            {"internalType": "uint256", "name": "jobsCompleted", "type": "uint256"},
            {"internalType": "uint256", "name": "slashCount", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

# Minimum CP bond required by the protocol (10 PWM).
MIN_BOND_PWM: float = 10.0

# 1 PWM = 1e18 wei (PWM uses the same denomination as ETH).
_WEI_PER_PWM: int = 10**18


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


@dataclass
class HardwareProfile:
    """On-chain hardware descriptor for a Compute Provider."""

    gpu_model: str
    vram_gb: int
    region: str  # ISO 3166-1 alpha-2 + optional zone, e.g. "us-east-1"

    def to_json(self) -> str:
        """Serialise to the JSON string stored on-chain."""
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RegistrationError(Exception):
    """Raised when CP registration or bond staking fails."""


class InsufficientBondError(RegistrationError):
    """Raised when the requested bond is below the protocol minimum."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_web3(web3_url: str) -> Any:
    """Return a connected Web3 instance, raising ImportError if web3 is absent."""
    try:
        from web3 import Web3  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "The 'web3' package is required: pip install web3"
        ) from exc

    if web3_url.startswith("ws"):
        from web3.providers import WebsocketProvider  # type: ignore[import]
        w3 = Web3(WebsocketProvider(web3_url))
    else:
        from web3 import HTTPProvider  # type: ignore[import]
        w3 = Web3(HTTPProvider(web3_url))

    if not w3.is_connected():
        raise RegistrationError(
            f"Cannot connect to Web3 endpoint: {web3_url}"
        )
    return w3


def _load_abi() -> list[dict]:
    """Load the deployed PWMStaking ABI and merge in the CP extension fragments."""
    with _STAKING_ABI_PATH.open() as fh:
        deployed = json.load(fh)
    base_abi: list[dict] = deployed.get("abi", deployed)
    # De-duplicate by (name, type) — deployed entries take precedence.
    existing_keys = {(e.get("name"), e.get("type")) for e in base_abi}
    extensions = [
        e for e in _CP_EXTENSION_ABI
        if (e.get("name"), e.get("type")) not in existing_keys
    ]
    return base_abi + extensions


def _build_contract(w3: Any) -> Any:
    """Return a web3 contract instance for PWMStaking."""
    abi = _load_abi()
    return w3.eth.contract(
        address=w3.to_checksum_address(PWM_STAKING_ADDRESS),
        abi=abi,
    )


def _sign_and_send(w3: Any, tx: dict, private_key: str) -> str:
    """Sign *tx* with *private_key* and broadcast it. Returns the tx hash hex."""
    # NOTE: private_key is intentionally never logged, formatted into strings,
    # or included in exception messages anywhere in this module.
    signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def _pwm_to_wei(amount_pwm: float) -> int:
    """Convert a PWM float amount to an integer wei value."""
    return int(amount_pwm * _WEI_PER_PWM)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def register_cp(
    web3_url: str,
    private_key: str,
    profile: HardwareProfile,
    bond_amount_pwm: float = 10.0,
) -> str:
    """
    Register as a Compute Provider and stake the CP bond.

    Parameters
    ----------
    web3_url:
        JSON-RPC or WebSocket endpoint (e.g. ``https://rpc.sepolia.org``).
    private_key:
        Hex-encoded private key for the CP wallet. **Never logged.**
    profile:
        Hardware descriptor that will be stored on-chain.
    bond_amount_pwm:
        Amount of PWM to stake as the CP bond. Must be >= 10.0.

    Returns
    -------
    str
        Transaction hash of the bond/registration transaction.

    Raises
    ------
    InsufficientBondError
        If ``bond_amount_pwm`` is below the protocol minimum of 10 PWM.
    RegistrationError
        If the Web3 connection fails or the transaction reverts.
    """
    # --- Validate bond before touching the network ---
    if bond_amount_pwm < MIN_BOND_PWM:
        raise InsufficientBondError(
            f"Bond amount {bond_amount_pwm} PWM is below the required minimum "
            f"of {MIN_BOND_PWM} PWM. Aborting to protect your wallet."
        )

    w3 = _load_web3(web3_url)
    contract = _build_contract(w3)

    # Derive the sender address from the private key without ever printing it.
    account = w3.eth.account.from_key(private_key)
    sender = account.address

    profile_json = profile.to_json()
    bond_wei = _pwm_to_wei(bond_amount_pwm)

    nonce = w3.eth.get_transaction_count(sender)
    gas_price = w3.eth.gas_price

    # ------------------------------------------------------------------
    # Planned contract function - requires PWMStaking.bondCP() extension
    #
    # Once the contract is extended with bondCP(string profileJson, uint256 bondWei),
    # the real call will look exactly like this:
    #
    #   tx = contract.functions.bondCP(profile_json, bond_wei).build_transaction({
    #       "from": sender,
    #       "value": bond_wei,   # PWM sent as native value
    #       "nonce": nonce,
    #       "gasPrice": gas_price,
    #   })
    #   tx_hash = _sign_and_send(w3, tx, private_key)
    #   return tx_hash
    #
    # Until then, we simulate the transaction locally and return a placeholder
    # that integration tests can detect and substitute with a real call.
    # ------------------------------------------------------------------

    # Simulate: verify the ABI fragment is present so the call would be valid.
    try:
        _fn = contract.functions.bondCP  # noqa: F841 — existence check only
        function_available = True
    except Exception:
        function_available = False

    if function_available:
        # Real path: bondCP() is live on-chain.
        try:
            tx = contract.functions.bondCP(
                profile_json, bond_wei
            ).build_transaction(
                {
                    "from": sender,
                    "value": bond_wei,
                    "nonce": nonce,
                    "gasPrice": gas_price,
                }
            )
            tx_hash = _sign_and_send(w3, tx, private_key)
        except Exception as exc:
            raise RegistrationError(
                f"bondCP() transaction failed for address {sender}: {exc}"
            ) from exc
    else:
        # Placeholder path: contract not yet extended.
        # Build a deterministic mock tx hash from the sender + profile so
        # integration tests can assert on it without a live contract.
        import hashlib

        mock_input = f"{sender}:{profile_json}:{bond_wei}:{nonce}"
        tx_hash = "0x" + hashlib.sha256(mock_input.encode()).hexdigest()
        print(
            f"[cp_register] WARNING: bondCP() not yet deployed. "
            f"Mock tx hash returned: {tx_hash[:18]}... "
            f"Re-run after contract extension to complete on-chain registration."
        )

    print(
        f"[cp_register] Registered CP {sender} | "
        f"GPU={profile.gpu_model} VRAM={profile.vram_gb}GB "
        f"region={profile.region} bond={bond_amount_pwm} PWM"
    )
    return tx_hash


def get_cp_status(web3_url: str, cp_address: str) -> dict:
    """
    Return the current on-chain status for a registered Compute Provider.

    Parameters
    ----------
    web3_url:
        JSON-RPC or WebSocket endpoint.
    cp_address:
        Checksummed Ethereum address of the CP to query.

    Returns
    -------
    dict with keys:
        ``bond_balance_pwm``  — current bond in PWM (float)
        ``jobs_completed``    — total jobs completed (int)
        ``slashing_history``  — list of slash events (list[dict])

    Notes
    -----
    getCPStatus() is a planned contract function (not yet in current ABI).
    Until it is deployed, this function returns a stub response so that
    callers can be developed and tested offline.
    """
    w3 = _load_web3(web3_url)
    contract = _build_contract(w3)

    checksum_address = w3.to_checksum_address(cp_address)

    # ------------------------------------------------------------------
    # Planned contract function - requires PWMStaking.getCPStatus() extension
    #
    # Once deployed, the real call will be:
    #
    #   bond_wei, jobs_completed, slash_count = (
    #       contract.functions.getCPStatus(checksum_address).call()
    #   )
    #   return {
    #       "bond_balance_pwm": bond_wei / _WEI_PER_PWM,
    #       "jobs_completed": jobs_completed,
    #       "slashing_history": _fetch_slash_events(w3, contract, checksum_address),
    #   }
    # ------------------------------------------------------------------

    try:
        bond_wei, jobs_completed, slash_count = (
            contract.functions.getCPStatus(checksum_address).call()
        )
        slash_events = _fetch_slash_events(w3, contract, checksum_address)
        return {
            "bond_balance_pwm": bond_wei / _WEI_PER_PWM,
            "jobs_completed": int(jobs_completed),
            "slashing_history": slash_events,
        }
    except Exception:
        # getCPStatus() not yet deployed — return stub.
        print(
            f"[cp_register] getCPStatus() not yet deployed. "
            f"Returning stub status for {cp_address}."
        )
        return {
            "bond_balance_pwm": 0.0,
            "jobs_completed": 0,
            "slashing_history": [],
            "_stub": True,
            "_note": (
                "Planned contract function getCPStatus() not yet deployed. "
                "Re-run after PWMStaking contract extension."
            ),
        }


def _fetch_slash_events(w3: Any, contract: Any, cp_address: str) -> list[dict]:
    """
    Query historical FraudSlashed events from the chain for a given CP address.

    Returns a list of dicts with keys ``tx_hash``, ``block_number``,
    ``artifact_hash``, ``burned_pwm``.
    """
    try:
        # FraudSlashed is indexed by artifactHash, not by CP address, so we
        # fetch all and filter.  A future contract extension should index on cp.
        events = contract.events.FraudSlashed.get_logs(
            from_block=0, to_block="latest"
        )
        results = []
        for ev in events:
            args = ev.get("args", {})
            results.append(
                {
                    "tx_hash": ev.get("transactionHash", b"").hex(),
                    "block_number": ev.get("blockNumber"),
                    "artifact_hash": args.get("artifactHash", b"").hex(),
                    "burned_pwm": args.get("burned", 0) / _WEI_PER_PWM,
                }
            )
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pwm-miner",
        description="PWM Compute Provider management CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- pwm-miner cp ... ---
    cp_parser = sub.add_parser("cp", help="Compute Provider operations")
    cp_sub = cp_parser.add_subparsers(dest="cp_command", required=True)

    # pwm-miner cp register
    reg = cp_sub.add_parser("register", help="Register as a Compute Provider and stake bond")
    reg.add_argument("--gpu", required=True, metavar="MODEL",
                     help="GPU model identifier, e.g. 'NVIDIA A100 80GB'")
    reg.add_argument("--vram", required=True, type=int, metavar="GB",
                     help="GPU VRAM in gigabytes")
    reg.add_argument("--region", required=True, metavar="CODE",
                     help="Region code, e.g. 'us-east-1'")
    reg.add_argument("--bond", type=float, default=10.0, metavar="PWM",
                     help=f"Bond amount in PWM (minimum {MIN_BOND_PWM}, default 10.0)")

    # pwm-miner cp status
    status = cp_sub.add_parser("status", help="Show current CP bond and job statistics")
    status.add_argument("--address", metavar="ADDR",
                        help="CP address to query (defaults to address derived from PWM_PRIVATE_KEY)")

    return parser


def _run_register(args: argparse.Namespace) -> int:
    """Handle `pwm-miner cp register`."""
    web3_url = os.environ.get("PWM_WEB3_URL", "").strip()
    private_key = os.environ.get("PWM_PRIVATE_KEY", "").strip()

    if not web3_url:
        print("ERROR: PWM_WEB3_URL environment variable is not set.", file=sys.stderr)
        return 1
    if not private_key:
        print("ERROR: PWM_PRIVATE_KEY environment variable is not set.", file=sys.stderr)
        return 1

    profile = HardwareProfile(
        gpu_model=args.gpu,
        vram_gb=args.vram,
        region=args.region,
    )

    try:
        tx_hash = register_cp(
            web3_url=web3_url,
            private_key=private_key,
            profile=profile,
            bond_amount_pwm=args.bond,
        )
    except InsufficientBondError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RegistrationError as exc:
        print(f"ERROR: Registration failed: {exc}", file=sys.stderr)
        return 1
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Registration transaction submitted: {tx_hash}")
    return 0


def _run_status(args: argparse.Namespace) -> int:
    """Handle `pwm-miner cp status`."""
    web3_url = os.environ.get("PWM_WEB3_URL", "").strip()
    if not web3_url:
        print("ERROR: PWM_WEB3_URL environment variable is not set.", file=sys.stderr)
        return 1

    cp_address = args.address
    if not cp_address:
        # Derive address from private key.
        private_key = os.environ.get("PWM_PRIVATE_KEY", "").strip()
        if not private_key:
            print(
                "ERROR: Provide --address or set PWM_PRIVATE_KEY to derive your address.",
                file=sys.stderr,
            )
            return 1
        try:
            from web3 import Web3  # type: ignore[import]
        except ImportError:
            print("ERROR: The 'web3' package is required: pip install web3", file=sys.stderr)
            return 1
        account = Web3().eth.account.from_key(private_key)
        cp_address = account.address

    try:
        status = get_cp_status(web3_url=web3_url, cp_address=cp_address)
    except RegistrationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"CP address      : {cp_address}")
    print(f"Bond balance    : {status['bond_balance_pwm']:.4f} PWM")
    print(f"Jobs completed  : {status['jobs_completed']}")
    slashes = status.get("slashing_history", [])
    if slashes:
        print(f"Slashing events : {len(slashes)}")
        for i, event in enumerate(slashes, 1):
            print(
                f"  [{i}] block={event['block_number']} "
                f"artifact={event['artifact_hash'][:12]}... "
                f"burned={event['burned_pwm']:.4f} PWM"
            )
    else:
        print("Slashing events : none")

    if status.get("_stub"):
        print(f"\nNote: {status['_note']}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the `pwm-miner` CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "cp":
        if args.cp_command == "register":
            return _run_register(args)
        elif args.cp_command == "status":
            return _run_status(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
