# Bounty #7 --- Genesis Principle Re-authoring (Tier B)

**Status:** SPEC PUBLISHED. Flips to **OPEN** at Phase 2 mainnet launch + 7 days
(per `DIRECTOR_ACTION_CHECKLIST.md` and `MVP_FIRST_STRATEGY.md` Phase E/F).

**Amount:** ~40,000 PWM total for Tier B (~20 principles x 2,000 PWM each),
drawn from the Bounty #7 pool of 168,000 PWM (Reserve-funded).

**Claim process:** first-come-first-served via `07-claims.md`.

**Payout:** per `07-genesis-principle-polish.md` --- pool-weight x 2,000 PWM
effective for Tier B (60% on triple-verify + 40% on >=2 distinct-SP L4
finalizations within 12 months).

**Reference exemplars:**
- `papers/Proof-of-Solution/mine_example/cassi.md` (1,595 lines) --- structural template
- `papers/Proof-of-Solution/mine_example/cacti.md` --- sibling-principle example
- `pwm-team/pwm_product/genesis/l{1,2,3}/L{1,2,3}-003.json` --- CASSI L1/L2/L3 JSON exemplar
- `pwm-team/pwm_product/genesis/l{1,2,3}/L{1,2,3}-004.json` --- CACTI L1/L2/L3 JSON exemplar

---

## Tier B --- 20 anchor principles

Selected to span **10 distinct physics domains** so early polishers seed
cluster conventions (`patterns.md`) across the broadest possible range of
the 500-principle registry. Every domain below gets at least one anchor;
domains with high expected miner demand get two.

### Principle table

| # | Principle | File | Cluster | Domain | Difficulty | Weight | Wanted expertise |
|---|-----------|------|---------|--------|------------|--------|------------------|
| 29 | CT (X-ray computed tomography) | `C_medical_imaging/029_ct.md` | C_medical_imaging | Imaging: CT | delta=3 (standard) | 20 | FBP / SART / MBIR / FBPConvNet |
| 30 | MRI (magnetic resonance imaging) | `C_medical_imaging/030_mri.md` | C_medical_imaging | Imaging: MRI | delta=3 (standard) | 20 | SENSE / GRAPPA / CG-SENSE, fastMRI contributor |
| 32 | Ultrasound (B-mode) | `C_medical_imaging/032_ultrasound.md` | C_medical_imaging | Imaging: ultrasound | delta=3 (standard) | 20 | DAS / plane-wave / min-variance beamformer |
| 42 | OCT (optical coherence tomography) | `C_medical_imaging/042_oct.md` | C_medical_imaging | Imaging: OCT | delta=3 (standard) | 20 | SSADA / phase-variance OCTA practitioner |
| 146 | NMR (nuclear magnetic resonance) | `L_spectroscopy/146_nmr.md` | L_spectroscopy | Spectroscopy: NMR | delta=3 (standard) | 20 | NMRPipe / CcpNmr Analysis / Bruker TopSpin |
| 137 | Raman imaging | `L_spectroscopy/137_raman_imaging.md` | L_spectroscopy | Spectroscopy: Raman | delta=3 (standard) | 20 | MCR-ALS / SpecNet / RamanNet |
| 140 | FTIR imaging | `L_spectroscopy/140_ftir_imaging.md` | L_spectroscopy | Spectroscopy: FTIR | delta=3 (standard) | 20 | Interferogram inversion / PLS / MCR-ALS |
| 180 | DNS (direct numerical simulation) | `R_fluid_dynamics/180_dns.md` | R_fluid_dynamics | Fluid dynamics: DNS | delta=5 (frontier) | 20 | JHTDB / NEK5000 / PyFR / spectral methods |
| 179 | LES (large eddy simulation) | `R_fluid_dynamics/179_les.md` | R_fluid_dynamics | Fluid dynamics: LES | delta=4 (advanced) | 20 | Smagorinsky / WALE / dynamic SGS models |
| 125 | X-ray crystallography (XRD) | `K_scientific_instrumentation/125_xray_crystallography.md` | K_scientific_instrumentation | Materials: XRD | delta=3 (standard) | 20 | Rietveld / Le Bail / ShelXL / GSAS-II |
| 85 | TEM (transmission electron microscopy) | `G_electron_microscopy/085_tem.md` | G_electron_microscopy | Materials: TEM | delta=3 (standard) | 20 | CTF-correction / RELION / cisTEM |
| 84 | SEM (scanning electron microscopy) | `G_electron_microscopy/084_sem.md` | G_electron_microscopy | Materials: SEM | delta=2 (accessible) | 20 | SE/BSE signal modeling / Montecarlo electron sim |
| 33 | PET (positron emission tomography) | `C_medical_imaging/033_pet.md` | C_medical_imaging | Medical: PET | delta=3 (standard) | 20 | MLEM / OSEM / TOF-PET reconstruction |
| 34 | SPECT (single-photon emission CT) | `C_medical_imaging/034_spect.md` | C_medical_imaging | Medical: SPECT | delta=3 (standard) | 20 | OSEM / collimator modeling / attenuation correction |
| 68 | EEG (electroencephalography) | `C_medical_imaging/068_eeg.md` | C_medical_imaging | Medical: EEG | delta=4 (advanced) | 20 | Source localization / LCMV / sLORETA / MNE-Python |
| 100 | SAR (synthetic aperture radar) | `I_remote_sensing/100_sar.md` | I_remote_sensing | Signal: radar | delta=4 (advanced) | 20 | Range-Doppler / omega-k / autofocus / ISCE |
| 101 | Sonar (active sonar imaging) | `I_remote_sensing/101_sonar.md` | I_remote_sensing | Signal: sonar | delta=3 (standard) | 20 | Matched filter / beamforming / SAS practitioner |
| 96 | Lidar (3D point cloud) | `H_depth_imaging/096_lidar.md` | H_depth_imaging | Signal: lidar | delta=3 (standard) | 20 | Time-of-flight / Geiger-mode / SLAM / PCL |
| 170 | Incompressible Navier-Stokes | `R_fluid_dynamics/170_incompressible_ns.md` | R_fluid_dynamics | Fluid dynamics: CFD | delta=3 (standard) | 20 | OpenFOAM / FEniCS / SIMPLE / PISO |
| 92 | Cryo-ET (cryo-electron tomography) | `G_electron_microscopy/092_cryoet.md` | G_electron_microscopy | Materials: cryo-ET | delta=4 (advanced) | 20 | CryoSPARC / IsoNet / cryoSTAR / IMOD |

### Summary by domain

| Domain group | Principles | Count |
|--------------|-----------|-------|
| Imaging (CT, MRI, ultrasound, OCT) | #29, #30, #32, #42 | 4 |
| Spectroscopy (NMR, Raman, FTIR) | #146, #137, #140 | 3 |
| Fluid dynamics (DNS, LES, incompressible NS) | #180, #179, #170 | 3 |
| Materials (XRD, TEM, SEM, cryo-ET) | #125, #85, #84, #92 | 4 |
| Medical (PET, SPECT, EEG) | #33, #34, #68 | 3 |
| Signal (radar/SAR, sonar, lidar) | #100, #101, #96 | 3 |
| **Total** | | **20** |

### Budget

**20 principles** x weight 20 x pool-weight formula = ~2,000 PWM each =
**~40,000 PWM** Tier B budget (from the 168,000 PWM Bounty #7 pool).

Two-stage payout per principle:
- **Stage 1 (60%):** ~1,200 PWM on triple-verify (3x ACCEPT from verifier agents, PR merged)
- **Stage 2 (40%):** ~800 PWM on minability (>=2 L4 certs from distinct SP wallets within 12 months)

---

## Acceptance criteria

Each claimed principle must satisfy ALL of the following before the 60%
verification payout triggers:

### 1. Triple-verified (mandatory)

Three verifier agents must independently issue ACCEPT:
- `agent-physics-verifier` --- physics correctness, dimensional analysis, kappa triples
- `agent-numerics-verifier` --- numerical consistency, epsilon thresholds, convergence claims
- `agent-cross-domain-verifier` --- sibling comparison, Jaccard distance from base-copy, patterns.md compliance

Any REVISE blocks payout until addressed. Any REJECT with physics flaws
means no payout; author may rework and resubmit as a new claim.

### 2. L1 + L2 + L3 JSONs matching schema

All three JSON layers must be present and parse cleanly:
- **L1** (`L1-<NNN>.json`): `artifact_id`, `E.forward_model`, `G.dag` with
  correctly derived `L_DAG`, `W.condition_number_{sub,kappa,effective}`,
  `physics_fingerprint` with principle-unique `sensing_mechanism`,
  `difficulty_delta` and `difficulty_tier` consistent, `mismatch_parameters`
  specific to this principle (NOT inherited from a sibling).
- **L2** (`L2-<NNN>.json`): `spec_range`, `benchmark_range`, `epsilon_fn`,
  `tiers` (T1--T4 + P_benchmark).
- **L3** (`L3-<NNN>.json`): dataset manifest with `dataset_hash` or public
  dataset citation with SHA-256, baseline solver table (3+ rows matching the
  sub-family's canonical baselines per `patterns.md`), `quality_scoring`
  ladder (4+ thresholds).

All fields must follow the schema demonstrated by L1/L2/L3-003 (CASSI) and
L1/L2/L3-004 (CACTI). Cross-reference `STYLE_NOTES.md` for naming
conventions.

### 3. Markdown walkthrough at cassi depth

Rewrite of `papers/Proof-of-Solution/mine_example/science/<cluster>/<NNN>_<slug>.md`
to mirror `cassi.md`'s section structure (1,400--1,700 lines). Must contain
real, principle-specific physics --- not widefield-templated placeholders.

### 4. No base-copy inheritance

The 3 verifier agents explicitly check for this. Physics-verifier catches
inherited kappa triples; cross-domain-verifier checks Jaccard distance.
Base-copies are REJECTED.

### 5. Local pre-check

Before submitting, run the structural parity check:
```bash
diff <(grep -E '^##[^#]|^### ' cassi.md | sed "s|CASSI|<Your Principle>|g") \
     <(grep -E '^##[^#]|^### ' <your-principle.md>)
# expected: empty (structural parity)
```

When `pwm-node` CLI is available, also run:
```bash
pwm-node verify --principle <NNN> --local
```

---

## Two-stage payout details

### Stage 1 --- Verification (60%)

1. Claim a principle slot in `07-claims.md` (FCFS).
2. Submit PR (`feat/principle-<NNN>-<slug>`) with `.md` walkthrough + L1/L2/L3 JSONs.
3. All 3 verifier agents issue ACCEPT.
4. agent-coord merges PR and calls:
   ```
   PWMReward.distribute(
     principle_hash = <L1-hash>,
     recipient       = <author_wallet>,
     amount          = ~1,200 PWM (60% of ~2,000)
   )
   ```
5. Principle's weight removed from Sigma (stabilizes future per-principle payouts).

### Stage 2 --- Minability (40%)

6. For 12 months post-merge, agent-coord monitors `PWMCertificate.Finalized`
   events filtered by `h_p = <this principle's L1-hash>`.
7. On the **second** finalized cert from a **distinct SP wallet**:
   ```
   PWMReward.distribute(
     principle_hash = <L1-hash>,
     recipient       = <author_wallet>,
     amount          = ~800 PWM (40% of ~2,000)
   )
   ```
8. If the 12-month window expires without 2 distinct-SP finalized certs,
   the 40% returns to Reserve via `PWMReward.returnToReserve()`.

---

## Difficulty tiers explained

| Difficulty | delta | Description | Examples in this list |
|------------|-------|-------------|---------------------|
| Accessible | 2 | Well-understood forward model, large public datasets | SEM (#84) |
| Standard | 3 | Established inverse problem, SOTA baselines exist | CT, MRI, ultrasound, OCT, NMR, Raman, FTIR, TEM, PET, SPECT, sonar, lidar, incompressible NS, XRD |
| Advanced | 4 | Complex forward model or limited public data | EEG, SAR, LES, cryo-ET |
| Frontier | 5 | Research-grade, no consensus SOTA | DNS |

Difficulty does NOT affect the Tier B payout (~2,000 PWM regardless). It
indicates the expected effort for a domain expert and the likelihood of the
40% minability payout triggering (higher delta = fewer miners = higher risk
of 40% expiring).

---

## How to expand Tier B later

Once 50% of Tier B claims settle (10+ principles triple-verified),
agent-coord can add more anchor principles as "Tier B+" entries (same
weight 20, same ~2,000 PWM payout) by appending to this file. Good
candidates for Tier B+:

- **A_microscopy**: #5 SIM, #8 FPM, #10 STED, #11 PALM/STORM, #17 Phase Contrast
- **B_compressive_imaging**: #26 SPC, #28 matrix sensing
- **C_medical_imaging**: #43 fMRI, #45 diffusion MRI, #41 PAT, #67 MEG
- **G_electron_microscopy**: #87 STEM, #88 4D-STEM
- **L_spectroscopy**: #145 UV-Vis, #147 XAS/EXAFS
- **R_fluid_dynamics**: #176 RANS k-epsilon, #182 Boussinesq, #194 FSI
- **U_electromagnetics**: #234 FDTD, #232 Maxwell full-wave
- **V_acoustics**: #265 acoustic beamforming, #257 acoustic wave
- **X_computational_chemistry**: DFT (principle # per agent-chemistry numbering)
- **AD_signal_processing**: #386 compressed sensing, #387 DOA estimation

Tier C opens rolling after 50% Tier B claimed; Tier D opens rolling
after 50% Tier C claimed (per `07-genesis-principle-polish.md` schedule).

---

## Why these 20 specifically

Selected for three reasons:

1. **Domain breadth** --- 10 physics domains rather than concentrating on
   imaging alone. Signal processing (radar, sonar, lidar), materials
   characterization (XRD, SEM, TEM, cryo-ET), medical source localization
   (EEG), nuclear medicine (PET, SPECT), and turbulence modeling (DNS, LES)
   all have active research communities that can contribute domain expertise
   the founding team lacks.

2. **Demand signal** --- modalities with active clinical, industrial, or
   research mining populations. CT, MRI, and PET have massive clinical
   installed bases; SAR has defense and Earth-observation demand; XRD is
   foundational to materials discovery; DNS/LES serve the CFD simulation
   market.

3. **Cluster seeding** --- each pattern-seeded cluster gets at least one
   anchor, and this list adds anchors to clusters not covered in the
   original spec (H_depth_imaging via lidar, I_remote_sensing via SAR/sonar,
   K_scientific_instrumentation via XRD). This ensures `patterns.md`
   conventions get established across the full registry width early.

Omitted deliberately: super-niche principles where 2,000 PWM exceeds the
expected author effort (most Tier C/D territory), and frontier-only
principles where the 40% minability payout is unlikely to trigger within
12 months (most delta=5 except DNS, which has JHTDB and established
benchmarks).

---

## Schedule

| Milestone | Trigger |
|-----------|---------|
| Tier B opens (this list becomes claimable) | Phase 2 mainnet launch + 7 days |
| Tier B+ expansion (optional) | 50% of Tier B claimed |
| Tier C opens (rolling) | 50% of Tier B claimed |
| Tier D opens (rolling) | 50% of Tier C claimed |
| Bounty closes | All 500 principles triple-verified OR 12 months post-launch (whichever first) |

---

## Contact / questions

Open a GitHub issue at `integritynoble/pwm-public` with the `bounty-07` label.
agent-coord triages within 48 hours.
