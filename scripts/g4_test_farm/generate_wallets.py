"""Generate 20 fresh random wallets for the STEP_3 G4 test farm.

Per `pwm-team/coordination/STEPS_3_6_7_PLAN.md` § STEP 3 Path B.
Saves to `$WALLETS_FILE` (default: `~/.pwm/g4-farm/wallets.json`)
which is OUTSIDE the repo. Private keys never enter git.

Usage:
    python scripts/g4_test_farm/generate_wallets.py
    python scripts/g4_test_farm/generate_wallets.py --count 20 --out ~/.pwm/g4-farm/wallets.json
    python scripts/g4_test_farm/generate_wallets.py --force-overwrite

The default behavior REFUSES to overwrite an existing wallets.json
(could destroy private keys). Pass --force-overwrite to override.

After running, run:
    python scripts/g4_test_farm/fund_wallets.py
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

DEFAULT_OUT = Path.home() / ".pwm" / "g4-farm" / "wallets.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--force-overwrite", action="store_true",
                    help="overwrite an existing wallets.json (destroys prior keys)")
    args = ap.parse_args()

    try:
        from eth_account import Account
    except ImportError:
        print("eth_account not installed. pip install eth_account", file=sys.stderr)
        return 1

    if args.out.exists() and not args.force_overwrite:
        print(f"REFUSING to overwrite existing {args.out}\n"
              f"Pass --force-overwrite to proceed (destroys existing private keys).",
              file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Make the parent dir owner-only readable.
    try:
        os.chmod(args.out.parent, 0o700)
    except Exception:
        pass

    wallets = []
    for i in range(args.count):
        # 32-byte random private key — eth_account validates + checksums.
        priv = "0x" + secrets.token_hex(32)
        acct = Account.from_key(priv)
        wallets.append({
            "index": i,
            "address": acct.address,
            "private_key": priv,
            "purpose": "g4_test_farm",
            "anchor": "L3-003" if i < 10 else "L3-004",
        })

    args.out.write_text(json.dumps(wallets, indent=2) + "\n")
    try:
        os.chmod(args.out, 0o600)  # owner-only
    except Exception:
        pass

    print(f"Generated {len(wallets)} wallets → {args.out}")
    print(f"  10 wallets assigned to L3-003 (CASSI)")
    print(f"  10 wallets assigned to L3-004 (CACTI)")
    print(f"\nFile permissions: 0o600 (owner read/write only)")
    print(f"Sample addresses:")
    for w in wallets[:3]:
        print(f"  [{w['index']:2d}] {w['address']}  → {w['anchor']}")
    print(f"  ... and {len(wallets) - 3} more")
    print(f"\nNext: python scripts/g4_test_farm/fund_wallets.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
