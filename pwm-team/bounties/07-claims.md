# Bounty #7 --- Active Claims Board (Tier B)

**First-come-first-served slot reservation for Tier B anchor principles.**

> **Also used for general L1/L2/L3 contributions (since 2026-05-03).**
> External contributors authoring a NEW Principle (outside the Tier B
> anchor list) use the same FCFS claim mechanism: open a GitHub issue
> titled `[L1 claim] L1-XXX <slug> — <author name>` and agent-coord
> reserves the next free numeric ID. Full flow + manifest schema +
> PR template are documented in
> `pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`.
>
> The Tier B claims table below is for anchor principles only; general
> contributions land at L1-532+ and don't need a dedicated table row
> (they're tracked via GitHub issues + PRs).

Full bounty rules: `07-genesis-principle-polish.md`
Tier B principle list and acceptance criteria: `07-genesis-priorities.md`
General contribution flow (any L1/L2/L3): `pwm-team/customer_guide/PWM_PRINCIPLE_CONTRIBUTION_GUIDE.md`

---

## How to claim a principle

1. **Choose an OPEN principle** from the table below.
2. **Open a PR** on `integritynoble/pwm-public` that adds your row to the
   "Tier B claims" table, OR open a GitHub issue with the label
   `bounty-07-claim` naming your principle number and wallet address.
3. **Include in your claim:**
   - Your GitHub handle
   - Your payout wallet address (Sepolia initially; mainnet PWM at launch)
   - A brief statement of domain expertise (1--2 sentences)
4. **agent-coord reviews within 48 hours** and confirms by editing the
   Status column from OPEN to CLAIMED. Claim is official only after
   agent-coord confirmation.

## Claim rules

- **Concurrent claims per author:** max 10 at once (prevents hoarding).
- **Claim lifetime:** 60 days from confirmation. If no PR with `.md`
  walkthrough + L1/L2/L3 JSON artifacts is opened within 60 days, the
  slot auto-releases (row moves to "Expired / released claims" below)
  and the principle becomes OPEN again.
- **Disputes:** if two claims arrive within the same 24h window,
  agent-coord reviews both and picks the one with stronger domain
  credentials. The other claimant can pick a different principle.
- **Voluntary release:** comment on the claim issue or PR to release
  your slot early.

## Payout summary (Tier B)

| Stage | % of ~2,000 PWM | Trigger |
|-------|-----------------|---------|
| Verification | 60% (~1,200 PWM) | 3x ACCEPT from verifier agents, PR merged |
| Minability | 40% (~800 PWM) | >=2 L4 certs from distinct SP wallets within 12 months |

---

## Tier B claims

| # | Principle | Domain | Claimed By | Wallet | Status | PR Link |
|---|-----------|--------|------------|--------|--------|---------|
| 29 | CT (X-ray computed tomography) | Imaging: CT | | | OPEN | |
| 30 | MRI (magnetic resonance imaging) | Imaging: MRI | | | OPEN | |
| 32 | Ultrasound (B-mode) | Imaging: ultrasound | | | OPEN | |
| 42 | OCT (optical coherence tomography) | Imaging: OCT | | | OPEN | |
| 146 | NMR (nuclear magnetic resonance) | Spectroscopy: NMR | | | OPEN | |
| 137 | Raman imaging | Spectroscopy: Raman | | | OPEN | |
| 140 | FTIR imaging | Spectroscopy: FTIR | | | OPEN | |
| 180 | DNS (direct numerical simulation) | Fluid dynamics: DNS | | | OPEN | |
| 179 | LES (large eddy simulation) | Fluid dynamics: LES | | | OPEN | |
| 170 | Incompressible Navier-Stokes | Fluid dynamics: CFD | | | OPEN | |
| 125 | X-ray crystallography (XRD) | Materials: XRD | | | OPEN | |
| 85 | TEM (transmission electron microscopy) | Materials: TEM | | | OPEN | |
| 84 | SEM (scanning electron microscopy) | Materials: SEM | | | OPEN | |
| 92 | Cryo-ET (cryo-electron tomography) | Materials: cryo-ET | | | OPEN | |
| 33 | PET (positron emission tomography) | Medical: PET | | | OPEN | |
| 34 | SPECT (single-photon emission CT) | Medical: SPECT | | | OPEN | |
| 68 | EEG (electroencephalography) | Medical: EEG | | | OPEN | |
| 100 | SAR (synthetic aperture radar) | Signal: radar | | | OPEN | |
| 101 | Sonar (active sonar imaging) | Signal: sonar | | | OPEN | |
| 96 | Lidar (3D point cloud) | Signal: lidar | | | OPEN | |

---

## Expired / released claims

Auto-populated by agent-coord when the 60-day no-PR window elapses OR
when an author voluntarily releases a claim.

| # | Principle | Claimant | Released | Reason |
|---|-----------|----------|----------|--------|
| (empty) | | | | |

---

## Merged / paid claims (Tier A + Tier B)

Claims that successfully triple-verified and received payout. For
post-hoc reporting and minability tracking.

| # | Principle | Author | Triple-verified | 60% paid | 2nd SP finalized | 40% paid |
|---|-----------|--------|-----------------|----------|------------------|----------|
| 25 | CASSI | founding team (Tier A --- no bounty) | 2026-04-21 | --- | --- | --- |
| 27 | CACTI | founding team (Tier A --- no bounty) | 2026-04-21 | --- | --- | --- |
| (Tier B claims accrue here as Phase F progresses) | | | | | | |

---

## Tier B claim statistics

| Metric | Value |
|--------|-------|
| Total Tier B principles | 20 |
| Claimed | 0 |
| In review | 0 |
| Triple-verified | 0 |
| Minability confirmed | 0 |
| Expired / released | 0 |
| Remaining OPEN | 20 |
| Tier B budget committed | ~40,000 PWM |
| Tier B budget paid | 0 PWM |

Updated by agent-coord at each claim status change.
