# PWM Event Indexer

`web3.py` + SQLite. Subscribes to `PWMRegistry`, `PWMCertificate`, `PWMReward`,
and `PWMTreasury` events; backfills from the deployment block and then polls
at 12 s intervals.

See the top-level [README](../README.md) for the full data flow. Run from
`infrastructure/agent-web/` with `PYTHONPATH=. python -m indexer.main`.
