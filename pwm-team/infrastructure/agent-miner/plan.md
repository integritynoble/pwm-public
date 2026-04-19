# agent-miner: Execution Plan

Read `CLAUDE.md` first (your role and all security requirements). This file is your step-by-step work order.

---

## Before You Start

- [ ] Read `CLAUDE.md` — security requirements are non-negotiable.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §Compute Provider, §Commit-then-Reveal.
- [ ] **Wait for M1.1** (contracts ABI) — you need `PWMCertificate` event stream schema.
- [ ] Check available before proceeding:
  - `../../coordination/agent-coord/interfaces/contracts_abi/PWMCertificate.json`
  - `../../coordination/agent-coord/interfaces/addresses.json`
- [ ] You can build `executor.py` and `docker/Dockerfile` immediately (no chain dependency).

---

## Step 1 — Docker Sandbox (start here — no dependencies)

- [ ] **1.1** Create `docker/Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim

  # No network access inside container
  RUN apt-get update && apt-get install -y --no-install-recommends \
      && rm -rf /var/lib/apt/lists/*

  # Non-root user
  RUN useradd -m -u 1000 miner
  USER miner

  # Mount points only — no host filesystem access
  WORKDIR /workspace
  VOLUME ["/input", "/output"]

  # Solver entry point injected at runtime
  CMD ["python", "/input/solve.py", "--input", "/input", "--output", "/output"]
  ```
- [ ] **1.2** Build and test locally:
  ```bash
  docker build -t pwm-sandbox docker/
  ```
- [ ] **1.3** Verify network isolation:
  ```bash
  docker run --network none pwm-sandbox python -c "import urllib.request; urllib.request.urlopen('http://example.com')"
  # Must fail with connection error
  ```
- [ ] **1.4** Verify no host filesystem access:
  ```bash
  docker run pwm-sandbox ls /home  # Should see only container /home, not host
  ```

---

## Step 2 — executor.py

- [ ] **2.1** Implement `execute_solver(solver_cid, instance_dir, output_dir, resource_limits) -> ExecutionResult`:
  ```python
  @dataclass
  class ExecutionResult:
      success: bool
      output_path: Path
      stdout: str
      stderr: str
      runtime_seconds: float
      memory_peak_mb: float
  ```
- [ ] **2.2** Steps inside `execute_solver()`:
  1. Fetch solver binary via `ipfs_fetch.fetch_solver(cid, expected_hash)`
  2. Verify SHA-256 BEFORE any execution
  3. Build docker run command with limits:
     ```bash
     docker run --network none \
       --memory {memory_limit_mb}m \
       --gpus {gpu_spec} \
       --runtime {timeout_seconds}s \
       -v {instance_dir}:/input:ro \
       -v {output_dir}:/output \
       pwm-sandbox python /input/solve.py
     ```
  4. Capture stdout/stderr
  5. Return ExecutionResult
- [ ] **2.3** If SHA-256 verification fails: raise `VerificationError`, do NOT run container.
- [ ] **2.4** Write `tests/test_executor.py` — test with a mock solver; confirm output captured.

---

## Step 3 — ipfs_fetch.py

- [ ] **3.1** `fetch_solver(cid: str, expected_hash: str) -> Path`:
  - Check local cache first (`~/.pwm_miner/cache/<cid>`)
  - If not cached: download from IPFS
  - Compute SHA-256 of downloaded file
  - If hash mismatch: delete file, raise `VerificationError`
  - If match: store in cache, return path
- [ ] **3.2** Write `tests/test_ipfs_fetch.py` — mock IPFS; test hash verification.

---

## Step 4 — cp_register.py (after M1.1)

- [ ] **4.1** `pwm-miner cp register --gpu <model> --vram <gb> --region <code>`:
  - Build hardware profile JSON
  - Stake ≥ 10 PWM as CP bond via `PWMCertificate.bondCP()`
  - Register profile on-chain
- [ ] **4.2** `pwm-miner cp status`:
  - Show current bond balance, slashing history, jobs completed

---

## Step 5 — job_queue.py (after M1.1)

- [ ] **5.1** Implement `JobQueue`:
  ```python
  class JobQueue:
      def poll(self) -> list[Job]:
          # Subscribe to PWMCertificate JobPosted events via WebSocket
          # Filter: job.compute_manifest.min_vram_gb <= local_vram
          # Return sorted by expected_reward desc

      def claim(self, job_id: str):
          # Mark job as claimed locally (prevent double-submit)
  ```
- [ ] **5.2** `Job` dataclass: `job_id`, `benchmark_hash`, `solver_cid`, `solver_sha256`, `compute_manifest`, `expected_reward`.
- [ ] **5.3** Write `tests/test_job_queue.py` — mock WebSocket events; confirm filtering by VRAM.

---

## Step 6 — commit_reveal.py (after M1.1)

This is the anti-front-running protocol. Implement carefully.

- [ ] **6.1** Implement `CommitRevealProtocol`:
  ```python
  class CommitRevealProtocol:
      def commit(self, job_id, solution_preview, nonce) -> str:
          # commit_hash = keccak256(solution_preview + nonce)
          # Call PWMCertificate.commit(job_id, commit_hash)
          # Return tx_hash

      def reveal(self, job_id, solution_preview, nonce) -> str:
          # Wait until block.timestamp >= job.commit_deadline (30s after job posted)
          # Call PWMCertificate.reveal(job_id, solution_preview, nonce)
          # Return tx_hash

      def run_job(self, job: Job) -> str:
          # 1. Execute solver: ExecutionResult = executor.execute_solver(...)
          # 2. Build solution_preview (first 32 bytes of output hash)
          # 3. nonce = os.urandom(32)
          # 4. self.commit(job.job_id, solution_preview, nonce)  ← must happen in 0–30s window
          # 5. Wait for reveal window (30–60s)
          # 6. self.reveal(job.job_id, solution_preview, nonce)
          # 7. Return cert_hash
  ```
- [ ] **6.2** Timing: commit window is 0–30s after job posted. If commit sent after 30s: abort this job.
- [ ] **6.3** Write `tests/test_commit_reveal.py` — simulate 3 CPs racing on same job; confirm first valid reveal wins.

---

## Step 7 — Main Loop

- [ ] **7.1** Create `pwm_miner/__main__.py`:
  ```python
  # Main CP mining loop
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
- [ ] **7.2** CLI entry point: `pwm-miner start [--vram-gb N] [--max-jobs N]`

---

## Step 8 — Integration Tests on Testnet

- [ ] **8.1** Run 100 consecutive job executions on testnet (using a known test solver).
- [ ] **8.2** Simulate racing: start 3 CP instances simultaneously on same job. Confirm first valid reveal wins and others get no reward.
- [ ] **8.3** Confirm Docker sandbox blocks network (run solver that tries to `curl` — must fail).
- [ ] **8.4** Confirm CP bond slashing on provably incorrect output (submit wrong output deliberately in test).

---

## Step 9 — Signal Completion

- [ ] **9.1** Update `../../coordination/agent-coord/progress.md` — mark M1.4 `DONE`.
- [ ] **9.2** Open PR: `feat/mining-client-v1`
  - Include: full `pwm_miner/` package, `docker/Dockerfile`, `tests/`
  - PR description: 100-job test result, race simulation result, sandbox verification
