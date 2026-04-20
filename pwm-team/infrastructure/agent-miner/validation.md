# agent-miner: Validation Checklist

Run every check below before merging the mining client PR. Security items are non-negotiable.

---

## V1 — Files Exist

- [ ] `pwm_miner/__init__.py`
- [ ] `pwm_miner/__main__.py` — main mining loop
- [ ] `pwm_miner/executor.py` — sandboxed solver execution
- [ ] `pwm_miner/ipfs_fetch.py` — download + hash verification
- [ ] `pwm_miner/job_queue.py` — event polling + job filtering
- [ ] `pwm_miner/commit_reveal.py` — anti-front-running protocol
- [ ] `pwm_miner/cp_register.py` — CP registration + bonding
- [ ] `docker/Dockerfile` — sandboxed execution environment
- [ ] `tests/test_executor.py`
- [ ] `tests/test_ipfs_fetch.py`
- [ ] `tests/test_job_queue.py`
- [ ] `tests/test_commit_reveal.py`

**Verify:**
```bash
pip install -e .
pwm-miner --help  # or python -m pwm_miner --help
```

---

## V2 — Docker Sandbox (SECURITY-CRITICAL)

### Dockerfile requirements:
- [ ] Base image: `python:3.11-slim`
- [ ] Non-root user created: `useradd -m -u 1000 miner` + `USER miner`
- [ ] Mount points: `/input` (read-only) and `/output` only
- [ ] No `pip install` of arbitrary packages at runtime
- [ ] CMD runs solver from `/input/solve.py`

### Network isolation test:
```bash
docker build -t pwm-sandbox docker/
docker run --network none pwm-sandbox python -c \
  "import urllib.request; urllib.request.urlopen('http://example.com')"
# MUST fail with connection error
```
- [ ] Network request fails inside container

### Host filesystem isolation test:
```bash
docker run pwm-sandbox ls /
# Should show container filesystem, NOT host filesystem
docker run pwm-sandbox cat /etc/hostname
# Should show container hostname, NOT host hostname
```
- [ ] No host filesystem access from inside container

### Root check:
```bash
docker run pwm-sandbox whoami
# Must print "miner", NOT "root"
```
- [ ] Container runs as non-root user

---

## V3 — executor.py

### ExecutionResult dataclass:
- [ ] `success: bool`
- [ ] `output_path: Path`
- [ ] `stdout: str`
- [ ] `stderr: str`
- [ ] `runtime_seconds: float`
- [ ] `memory_peak_mb: float`

### execute_solver() flow:
1. [ ] Fetches solver via `ipfs_fetch.fetch_solver(cid, expected_hash)`
2. [ ] Verifies SHA-256 BEFORE any execution
3. [ ] Builds docker run command with limits:
   ```bash
   docker run --network none \
     --memory {memory_limit_mb}m \
     --gpus {gpu_spec} \
     --timeout {timeout_seconds} \
     -v {instance_dir}:/input:ro \
     -v {output_dir}:/output \
     pwm-sandbox python /input/solve.py
   ```
4. [ ] `/input` mounted read-only (`:ro` flag)
5. [ ] Captures stdout and stderr
6. [ ] Returns ExecutionResult

### SHA-256 failure behavior:
- [ ] If hash mismatch: raises `VerificationError`
- [ ] Container is NEVER started if hash fails
- [ ] No partial execution occurs

**Test:**
```bash
pytest tests/test_executor.py -v
```
- [ ] Mock solver produces expected output
- [ ] Resource limits enforced (memory, timeout)
- [ ] Hash mismatch → VerificationError raised, no container started

---

## V4 — ipfs_fetch.py

- [ ] `fetch_solver(cid: str, expected_hash: str) -> Path`
- [ ] Checks local cache first: `~/.pwm_miner/cache/<cid>`
- [ ] If not cached: downloads from IPFS
- [ ] Computes SHA-256 of downloaded file
- [ ] If hash mismatch: deletes file, raises `VerificationError`
- [ ] If match: stores in cache, returns path
- [ ] Never returns a path to an unverified file

**Test:**
```bash
pytest tests/test_ipfs_fetch.py -v
```
- [ ] Correct hash → file cached and returned
- [ ] Wrong hash → VerificationError raised, file deleted
- [ ] Cached file → no re-download (fast path)

---

## V5 — job_queue.py

### JobQueue class:
- [ ] `poll() -> list[Job]` — subscribes to `PWMCertificate.JobPosted` events via WebSocket
- [ ] Filters: skip if `compute_manifest.min_vram_gb > local_vram`
- [ ] Returns jobs sorted by `expected_reward` descending
- [ ] `claim(job_id: str)` — marks job as claimed locally (prevents double-submit)

### Job dataclass:
- [ ] `job_id: str`
- [ ] `benchmark_hash: str`
- [ ] `solver_cid: str`
- [ ] `solver_sha256: str`
- [ ] `compute_manifest: dict`
- [ ] `expected_reward: float`

**Test:**
```bash
pytest tests/test_job_queue.py -v
```
- [ ] Mock WebSocket events parsed correctly
- [ ] Jobs filtered by VRAM requirement
- [ ] Jobs sorted by expected reward
- [ ] Claimed jobs not returned on subsequent polls

---

## V6 — commit_reveal.py (TIMING-CRITICAL)

### Protocol timing (canonical — 60-second window):

```
t=0:     Job posted on-chain
t=0-30s: Phase 1 — CP commits hash(solution_preview + nonce)
t=30-60s: Phase 2 — CP reveals solution_preview + nonce
```

### CommitRevealProtocol class:

- [ ] `commit(job_id, solution_preview, nonce) -> tx_hash`
  - commit_hash = `keccak256(solution_preview + nonce)`
  - Calls `PWMCertificate.commit(job_id, commit_hash)`

- [ ] `reveal(job_id, solution_preview, nonce) -> tx_hash`
  - Waits until `block.timestamp >= job.commit_deadline` (30s after job posted)
  - Calls `PWMCertificate.reveal(job_id, solution_preview, nonce)`
  - Contract verifies commit matches

- [ ] `run_job(job: Job) -> cert_hash`
  1. Execute solver: `executor.execute_solver(...)`
  2. Build solution_preview (first 32 bytes of output hash)
  3. nonce = `os.urandom(32)`
  4. `self.commit(...)` — must happen within 0-30s window
  5. Wait for reveal window (30-60s)
  6. `self.reveal(...)`
  7. Return cert_hash

### Timing enforcement:
- [ ] If commit would be sent after 30s: abort job, do not commit
- [ ] Race winner: first valid Phase 2 reveal earns `(1-p) × 55%`
- [ ] Tie-breaking: earlier block.timestamp wins

**Test:**
```bash
pytest tests/test_commit_reveal.py -v
```
- [ ] Simulates 3 CPs racing on same job
- [ ] First valid reveal wins
- [ ] Late commit (>30s) → job aborted
- [ ] Reveal before commit deadline → reverts

---

## V7 — cp_register.py

```bash
pwm-miner cp register --gpu <model> --vram <gb> --region <code>
pwm-miner cp status
```

- [ ] Builds hardware profile JSON
- [ ] Stakes ≥ 10 PWM as CP bond (calls `PWMCertificate.bondCP()`)
- [ ] Registers profile on-chain
- [ ] `cp status` shows: bond balance, slashing history, jobs completed

---

## V8 — Main Loop (__main__.py)

```python
queue = JobQueue()
protocol = CommitRevealProtocol()

while True:
    jobs = queue.poll()
    for job in jobs:
        try:
            cert_hash = protocol.run_job(job)
            print(f"Submitted cert: {cert_hash}")
        except VerificationError as e:
            print(f"SECURITY: rejected job {job.job_id}: {e}")
        except Exception as e:
            print(f"Job {job.job_id} failed: {e}")
    time.sleep(5)
```

- [ ] CLI entry point: `pwm-miner start [--vram-gb N] [--max-jobs N]`
- [ ] VerificationError triggers SECURITY log (distinguishable from normal errors)
- [ ] Graceful shutdown on SIGINT/SIGTERM
- [ ] 5-second poll interval between job checks

---

## V9 — Spot-Check Verification Constants

These are protocol-level (not implemented by miner, but miner must be aware):

| Parameter | Value |
|-----------|-------|
| Spot-check rate | 5% of all completed jobs |
| Match outcome | CP reputation +1 |
| Mismatch outcome | CP slashed 50%, 50% to validator, reward clawed back |
| Ban threshold | 3 mismatches in 30 days → 100% slash + address banned |

- [ ] Miner code does NOT try to detect or evade spot-checks
- [ ] Miner always submits honest results (no output manipulation)

---

## V10 — Security Audit Checklist

- [ ] **NEVER** executes solver binary without SHA-256 match verified
- [ ] **NEVER** gives solver container network access (--network none)
- [ ] **NEVER** gives solver container host filesystem access
- [ ] **NEVER** runs solver as root inside container
- [ ] Private key handling: read from env, never logged/printed
- [ ] No shell injection: solver path/args properly escaped
- [ ] No TOCTOU: hash verified immediately before docker run (no gap)

```bash
# Grep for security anti-patterns
grep -rn "shell=True" pwm_miner/     # Should be zero matches or carefully reviewed
grep -rn "PRIVATE_KEY" pwm_miner/    # Only env read, never print/log
grep -rn "network" docker/Dockerfile  # Should not enable networking
```

---

## V11 — Integration Tests on Testnet

- [ ] 100 consecutive job executions completed successfully
- [ ] Racing test: 3 CP instances on same job, first valid reveal wins
- [ ] Docker sandbox blocks network (solver `curl` attempt fails)
- [ ] CP bond slashing works on provably incorrect output
- [ ] All results documented in PR description
