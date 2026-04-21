"""
Main CP mining loop and CLI entry point.

Usage:
    pwm-miner start [--vram-gb N] [--max-jobs N]
    pwm-miner cp register --gpu <model> --vram <gb> --region <code>
    pwm-miner cp status [--address <addr>]

Environment variables:
    PWM_WEB3_URL        — JSON-RPC / WebSocket endpoint (Sepolia default)
    PWM_PRIVATE_KEY     — Wallet private key for signing transactions
    PWM_CERTIFICATE_ADDR — PWMCertificate contract address (default: Sepolia)
    PWM_LOCAL_VRAM_GB   — VRAM override (also settable via --vram-gb)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time

from .commit_reveal import CommitRevealProtocol
from .ipfs_fetch import VerificationError
from .job_queue import JobQueue

logger = logging.getLogger("pwm_miner")

_DEFAULT_WEB3_URL = "wss://sepolia.infura.io/ws/v3/YOUR_PROJECT_ID"
_DEFAULT_CERTIFICATE_ADDR = "0x8963b60454EC1D9F65eE3cbF7aBC5D1220C3dB08"
_POLL_INTERVAL_SECONDS = 5


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def run_miner(
    web3_url: str,
    private_key: str,
    certificate_addr: str,
    vram_gb: int,
    max_jobs: int,
    instance_base: str,
) -> None:
    """Core mining loop — polls for jobs and runs commit-reveal on each."""
    from pathlib import Path

    queue = JobQueue(web3_url=web3_url, local_vram_gb=vram_gb)
    protocol = CommitRevealProtocol(
        web3_url=web3_url,
        private_key=private_key,
        contract_address=certificate_addr,
        instance_base=Path(instance_base),
    )

    logger.info("PWM miner started (vram_gb=%d, max_jobs=%d)", vram_gb, max_jobs)

    active_jobs = 0
    while True:
        try:
            jobs = queue.poll()
        except Exception as exc:
            logger.warning("poll() failed: %s", exc)
            time.sleep(_POLL_INTERVAL_SECONDS)
            continue

        for job in jobs:
            if max_jobs and active_jobs >= max_jobs:
                logger.debug("max_jobs=%d reached, skipping %s", max_jobs, job.job_id)
                break

            queue.claim(job.job_id)
            active_jobs += 1

            try:
                cert_hash = protocol.run_job(job)
                logger.info("Submitted cert %s for job %s", cert_hash, job.job_id)
            except VerificationError as exc:
                logger.error("SECURITY: rejected job %s — %s", job.job_id, exc)
            except Exception as exc:
                logger.warning("Job %s failed: %s", job.job_id, exc)

        time.sleep(_POLL_INTERVAL_SECONDS)


def _cmd_start(args: argparse.Namespace) -> None:
    web3_url = os.environ.get("PWM_WEB3_URL", _DEFAULT_WEB3_URL)
    private_key = os.environ.get("PWM_PRIVATE_KEY", "")
    if not private_key:
        sys.exit("Error: PWM_PRIVATE_KEY environment variable is required")

    certificate_addr = os.environ.get("PWM_CERTIFICATE_ADDR", _DEFAULT_CERTIFICATE_ADDR)
    vram_gb = args.vram_gb if args.vram_gb is not None else int(os.environ.get("PWM_LOCAL_VRAM_GB", "0"))
    max_jobs = args.max_jobs or 0
    instance_base = os.environ.get("PWM_INSTANCE_DIR", "/tmp/pwm_miner/instances")

    run_miner(
        web3_url=web3_url,
        private_key=private_key,
        certificate_addr=certificate_addr,
        vram_gb=vram_gb,
        max_jobs=max_jobs,
        instance_base=instance_base,
    )


def _cmd_cp(args: argparse.Namespace) -> None:
    from .cp_register import main as cp_main
    cp_main()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pwm-miner",
        description="PWM Compute Provider mining client",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    start_p = sub.add_parser("start", help="Start mining loop")
    start_p.add_argument("--vram-gb", type=int, default=None, metavar="N", help="Local VRAM in GB")
    start_p.add_argument("--max-jobs", type=int, default=0, metavar="N", help="Stop after N jobs (0=unlimited)")
    start_p.set_defaults(func=_cmd_start)

    cp_p = sub.add_parser("cp", help="Compute Provider management")
    cp_p.set_defaults(func=_cmd_cp)

    args = parser.parse_args()
    _setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
