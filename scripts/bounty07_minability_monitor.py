"""Bounty #7 minability-payout monitor.

Polls PWMCertificate for Finalized events, groups certs by h_p (principle
hash), and triggers the 40% minability tranche when a Bounty #7 principle
accumulates ≥ 2 finalizations from distinct SP wallets within 12 months
of its triple-verified date.

Per MVP_FIRST_STRATEGY.md §Phase F and DIRECTOR_ACTION_CHECKLIST.md §5.5.

## Usage

    export PWM_WEB3_URL=https://sepolia.infura.io/v3/<key>
    export PWM_PRIVATE_KEY=<agent-coord multisig key>    # or hardware-wallet
    export PWM_BOUNTY_STATE=./bounty07_state.json        # persistent state

    python3 scripts/bounty07_minability_monitor.py \
        --poll-interval 3600 \
        --state-file $PWM_BOUNTY_STATE

## State shape

    {
      "last_processed_block": 5123456,
      "principles": {
        "L1-012": {
          "h_p": "0x...",
          "author_wallet": "0x...",
          "verified_date": "2026-05-01",
          "tier_weight": 20,
          "payout_total_pwm": 2000,
          "distinct_sp_wallets": ["0xA...", "0xB..."],
          "minability_paid": true,
          "minability_tx": "0x..."
        },
        ...
      }
    }

## Action logic per event

For each PWMCertificate.Finalized event:
  1. Read h_p from event
  2. Find principle in state (lookup by h_p → artifact_id)
  3. If artifact_id not in Bounty #7 program → skip (also skips Tier A
     CASSI/CACTI which are founding-team done)
  4. If 12-month minability window expired → skip + flag for Reserve return
  5. Add sp_wallet to distinct_sp_wallets set
  6. If len(distinct_sp_wallets) >= 2 AND not minability_paid:
       Call PWMReward.distribute(h_p, author_wallet, 0.40 × payout_total_pwm)
       Mark minability_paid = True, store minability_tx
  7. Persist state to disk

## Reserve return (periodic sweep)

Separate sweep runs daily: for each principle where
(now - verified_date) > 12 months AND minability_paid == False:
  Call PWMReward.returnToReserve(0.40 × payout_total_pwm,
                                   reason="bounty_7_minability_window_expired")
  Mark as window_expired in state
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("bounty07_monitor")


@dataclass
class PrincipleState:
    """Track one Bounty #7 principle through the minability gate."""
    artifact_id: str                     # e.g. "L1-012"
    h_p: str                              # on-chain principle hash (0x-prefixed)
    author_wallet: str                    # 0x-prefixed author address
    verified_date: str                    # ISO-8601 date string
    tier_weight: int                      # 20 / 5 / 1 for Tier B/C/D
    payout_total_pwm: int                 # per-principle effective payout
    distinct_sp_wallets: list[str] = field(default_factory=list)
    minability_paid: bool = False
    minability_tx: str | None = None
    window_expired: bool = False


@dataclass
class MonitorState:
    last_processed_block: int = 0
    principles: dict[str, PrincipleState] = field(default_factory=dict)


# ───── persistence ─────


def load_state(path: Path) -> MonitorState:
    if not path.exists():
        return MonitorState()
    data = json.loads(path.read_text())
    ps = {
        k: PrincipleState(**v) for k, v in data.get("principles", {}).items()
    }
    return MonitorState(
        last_processed_block=data.get("last_processed_block", 0),
        principles=ps,
    )


def save_state(state: MonitorState, path: Path) -> None:
    data = {
        "last_processed_block": state.last_processed_block,
        "principles": {k: asdict(v) for k, v in state.principles.items()},
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


# ───── event processing ─────


def process_event(state: MonitorState, event: dict) -> bool:
    """Handle one Finalized event. Returns True if a state change occurred."""
    h_p = event["args"]["h_p"]
    sp_wallet = event["args"]["sp_wallet"]

    # Find the principle this event belongs to
    principle = None
    for p in state.principles.values():
        if p.h_p.lower() == h_p.lower():
            principle = p
            break
    if principle is None:
        logger.debug("event for unknown h_p (not in Bounty #7 program): %s", h_p)
        return False

    if principle.window_expired or principle.minability_paid:
        logger.debug("principle %s window closed or already paid", principle.artifact_id)
        return False

    # 12-month window check
    verified = datetime.fromisoformat(principle.verified_date).date()
    if date.today() - verified > timedelta(days=365):
        principle.window_expired = True
        logger.info("principle %s minability window expired (>365d since verify)", principle.artifact_id)
        # The actual returnToReserve call happens in the daily sweep
        return True

    if sp_wallet.lower() in (w.lower() for w in principle.distinct_sp_wallets):
        logger.debug("duplicate SP wallet for %s: %s", principle.artifact_id, sp_wallet)
        return False

    principle.distinct_sp_wallets.append(sp_wallet)
    logger.info(
        "principle %s: +1 distinct SP wallet (%s), now %d",
        principle.artifact_id,
        sp_wallet,
        len(principle.distinct_sp_wallets),
    )

    if len(principle.distinct_sp_wallets) >= 2 and not principle.minability_paid:
        # Trigger minability payout
        tx = _pay_minability_tranche(principle)
        principle.minability_paid = True
        principle.minability_tx = tx
        logger.info(
            "principle %s: MINABILITY PAID — %d PWM to %s, tx %s",
            principle.artifact_id,
            int(principle.payout_total_pwm * 0.40),
            principle.author_wallet,
            tx,
        )
    return True


def _pay_minability_tranche(principle: PrincipleState) -> str:
    """Call PWMReward.distribute() for 40% of payout. Returns tx hash.

    Implementation stub — replace with real web3 call at deploy time.
    """
    amount = int(principle.payout_total_pwm * 0.40)
    # TODO: real call:
    #   chain = PWMChain(network='mainnet')
    #   tx_hash = chain.w3.eth.contract(...).functions.distribute(
    #       principle.h_p, principle.author_wallet, amount * 10**18
    #   ).transact({"from": coord_multisig})
    return f"0x_stub_{principle.artifact_id}_minability"


def daily_sweep(state: MonitorState) -> int:
    """Check every principle for expired minability windows. Returns count returned."""
    returned = 0
    today = date.today()
    for p in state.principles.values():
        if p.minability_paid or p.window_expired:
            continue
        verified = datetime.fromisoformat(p.verified_date).date()
        if today - verified > timedelta(days=365):
            _return_to_reserve(p)
            p.window_expired = True
            returned += 1
    return returned


def _return_to_reserve(principle: PrincipleState) -> None:
    """Call PWMReward.returnToReserve() for the unpaid 40%."""
    amount = int(principle.payout_total_pwm * 0.40)
    # TODO: real call:
    #   chain = PWMChain(network='mainnet')
    #   chain.w3.eth.contract(...).functions.returnToReserve(
    #       principle.h_p, amount, "bounty_7_minability_window_expired"
    #   ).transact({"from": coord_multisig})
    logger.info(
        "principle %s: 40%% (%d PWM) returned to Reserve (window expired)",
        principle.artifact_id,
        amount,
    )


# ───── main loop ─────


def fetch_events(start_block: int, end_block: int) -> list[dict]:
    """Fetch PWMCertificate.Finalized events between blocks.

    Stub — replace with real web3 log query at deploy time.
    """
    # TODO: real implementation:
    #   chain = PWMChain(network='mainnet')
    #   cert_contract = chain.contracts['PWMCertificate'].contract
    #   filt = cert_contract.events.Finalized.create_filter(
    #       fromBlock=start_block, toBlock=end_block
    #   )
    #   return [dict(e) for e in filt.get_all_entries()]
    return []


def run_once(state: MonitorState, state_path: Path) -> None:
    """One polling iteration."""
    try:
        current_block = _current_block()
    except Exception as e:
        logger.warning("cannot query current block: %s", e)
        return

    if state.last_processed_block == 0:
        state.last_processed_block = max(0, current_block - 1000)

    events = fetch_events(state.last_processed_block + 1, current_block)
    changed = False
    for ev in events:
        if process_event(state, ev):
            changed = True
    state.last_processed_block = current_block

    if daily_sweep(state) > 0:
        changed = True

    if changed or events:
        save_state(state, state_path)


def _current_block() -> int:
    """Stub for the current block number. Real impl uses PWMChain.block_number()."""
    return int(time.time()) // 12  # Sepolia ~12s/block


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Bounty #7 minability monitor")
    ap.add_argument("--state-file", type=Path, default=Path("bounty07_state.json"))
    ap.add_argument("--poll-interval", type=int, default=3600, help="seconds between polls")
    ap.add_argument("--once", action="store_true", help="run once and exit (for testing)")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    state = load_state(args.state_file)
    logger.info("loaded state: %d principles tracked, last block %d",
                len(state.principles), state.last_processed_block)

    if args.once:
        run_once(state, args.state_file)
        return 0

    logger.info("polling every %ds", args.poll_interval)
    while True:
        try:
            run_once(state, args.state_file)
        except KeyboardInterrupt:
            logger.info("interrupted; saving state and exiting")
            save_state(state, args.state_file)
            return 130
        except Exception as e:
            logger.exception("unexpected error in poll loop: %s", e)
        time.sleep(args.poll_interval)


if __name__ == "__main__":
    sys.exit(main())
