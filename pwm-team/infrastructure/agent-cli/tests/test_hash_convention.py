"""Regression test: lock in the on-chain hash convention.

The agent-cli's `mine.py::_build_cert_payload` must produce benchmarkHash
values that match what `scripts/register_genesis.py` writes to
PWMRegistry. Both use keccak256(canonical_json) where
canonical_json = json.dumps(sort_keys=True, separators=(",", ":")).

An earlier JS variant (scripts/register_genesis.js) used
JSON.stringify, which drops trailing `.0` on floats and therefore
produces different hashes. That script is deprecated, but this test
guards against any future canonical-serializer change silently breaking
the on-chain↔CLI compatibility.

Reference values pinned below are the actual Sepolia on-chain hashes
from the CASSI + CACTI genesis registration (git commit b7cbc0a;
blocks 10703851–10703857). If you're changing canonical JSON for a
good reason, you also need to re-register genesis artifacts under the
new hashes — so the divergence is a real deploy event, not a test tweak.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from pwm_node.commands.mine import _canonical_json, _keccak256_hex


# repo_root = .../pwm/ (parent of pwm-team/)
# this test file = .../pwm-team/infrastructure/agent-cli/tests/test_hash_convention.py
# parents[4] = .../pwm/
REPO_ROOT = Path(__file__).resolve().parents[4]
GENESIS_DIR = REPO_ROOT / "pwm-team" / "pwm_product" / "genesis"

# Known on-chain values from the Sepolia genesis registration (commit b7cbc0a).
# See scripts/register_genesis_sepolia.py run output + the 100-cert run (which
# used the L3-003 hash below as benchmarkHash on every submission).
ONCHAIN_SEPOLIA_HASHES = {
    "L1-003": "0xe3b1328c66835cd729fa50650ef1d1bac4aa407807d6d97d4979e988a99a51ea",
    "L2-003": "0x471e7017692cde623cee2741e751413cfb4752457429f128c0004174fea86896",
    "L3-003": "0xdc8ad0dc68682eff750188c8d4d84179b3f7deddee1af562bc3b085794048b4a",
    "L1-004": "0xa2ae37946ef2822a308a4e60245dd2655070190cf8f3913559ae36286b26a56b",
    "L2-004": "0x3d15686eff5758f77fac1ae4843e25499a87d0f5fcd2661023eb1b69228aa8f9",
    "L3-004": "0x052324ba0585e4cf320914e117bf9b08656d602b9ac753b289a6a75ba926eab4",
}


@pytest.mark.parametrize("artifact_id,expected_hash", ONCHAIN_SEPOLIA_HASHES.items())
def test_genesis_artifact_hash_matches_onchain(artifact_id: str, expected_hash: str):
    """mine.py hash convention must reproduce the Sepolia on-chain hash.

    A failure here means either:
      (a) the canonical-JSON serializer in mine.py changed silently, or
      (b) the genesis JSON file was modified after registration.
    Either is a red flag that deserves investigation before shipping.
    """
    import json
    layer = artifact_id.split("-")[0].lower()  # l1 / l2 / l3
    path = GENESIS_DIR / layer / f"{artifact_id}.json"
    assert path.is_file(), f"missing genesis artifact: {path}"

    obj = json.loads(path.read_text())
    computed = _keccak256_hex(_canonical_json(obj))
    assert computed == expected_hash, (
        f"{artifact_id} hash divergence:\n"
        f"  expected (on-chain): {expected_hash}\n"
        f"  computed (this CLI): {computed}\n"
        f"Either mine.py's canonical-JSON or the artifact file changed. "
        f"Investigate before deploying — the CLI will not be able to "
        f"submit certs against the currently-registered benchmarkHash."
    )
