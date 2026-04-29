# Medical imaging v3 standalone Principles — genesis candidates

**Date:** 2026-04-29
**Owner:** Director
**Audience:** Director, Principle authors, deploy planners
**Status:** candidate list — Director picks 2-5 for genesis batch
**Cross-references:**
- `pwm-team/pwm_product/genesis/PWM_V3_STANDALONE_VS_COMPOSITE.md` (the design recommendation that admits standalone multi-physics)
- `pwm-team/pwm_product/genesis/PWM_V3_GENESIS_NOW.md` (the operational paths A/B/C)
- `pwm-team/pwm_product/genesis/PWM_V2_GENESIS_INCLUSION.md` (parallel v2 PWDR batch)
- Existing genesis: `pwm-team/content/agent-imaging/principles/C_medical_imaging/`, `O_multimodal_fusion/`

---

## TL;DR

Director prefers medical imaging for the v3 standalone genesis batch. After auditing the current 142 imaging Principles + 6 multimodal-fusion Principles, **eight clean v3 candidates** are not in current genesis but are widely-cited multi-physics medical imaging methods with joint coupled forward models. Top recommendations:

| # | Method | Joint physics | L_DAG | Clinical status |
|---|---|---|---|---|
| 1 | **Quantitative Susceptibility Mapping (QSM)** | MR phase + Maxwell magnetostatics + dipole inversion | ~6-8 | clinically deployed (neuro, deep-brain stim) |
| 2 | **Quantitative PAT (qPAT)** | Optical absorption + thermoelastic + acoustic | ~7-9 | research/early clinical (oncology, vascular) |
| 3 | **Pharmacokinetic dynamic PET (PK-PET)** | Photon transport + ODE tracer kinetics | ~6-8 | clinical research (quantitative oncology) |
| 4 | **Hyperpolarized 13C metabolic MRI** | DNP physics + chemical exchange + MR readout | ~8-10 | research/early clinical (cancer metabolism) |
| 5 | **Joint MEG-EEG source imaging** | Maxwell magnetostatics + electrostatics + neural sources | ~7-9 | clinical (epilepsy, presurgical mapping) |

Plus three additional candidates:

| # | Method | Notes |
|---|---|---|
| 6 | Optical Coherence Elastography (OCE) | OCT + tissue mechanics; emerging ophthalmology |
| 7 | Photoacoustic-Ultrasound dual-mode (PAUS) | PAT + US joint imaging |
| 8 | Cardiac 4D-flow MRI with hemodynamic biomechanics | MR + Navier-Stokes in heart chambers |

**Director's recommended Path A pick (2 Principles):** QSM + qPAT — both clinically established, both have decades of joint-physics theory, both fit cleanly in the existing `C_medical_imaging/` subtree.

---

## Audit: what's already in current medical imaging genesis

### Single-physics or simplified forward models (cannot duplicate)

The current 41 medical imaging Principles in `C_medical_imaging/` cover the standard modalities individually:

```
L1-029 CT          L1-052 brachytherapy       L1-064 CLE
L1-030 MRI         L1-053 portal_imaging      L1-065 fNIRS
L1-031 X-ray       L1-054 photon_counting_CT  L1-066 EIT
L1-032 ultrasound  L1-055 MRE                 L1-067 MEG
L1-033 PET         L1-056 CEST MRI            L1-068 EEG
L1-034 SPECT       L1-057 ASL MRI             L1-069 MPI
L1-035 fluoroscopy L1-058 MRA
L1-036 mammography L1-059 SWI
L1-037 DEXA        L1-060 MRF
L1-038 CBCT        L1-061 IVUS
L1-039 X-ray angio L1-062 CEUS
L1-040 DOT         L1-063 DBT
L1-041 PAT         L1-042 OCT
L1-043 fMRI        L1-044 MRS
L1-045 diffusion MRI                          L1-046 Doppler US
L1-047 elastography                           L1-048 fiber endoscopy
L1-049 fundus      L1-050 OCTA                L1-051 proton therapy
```

Critical observation: **several of these have simplified single-physics forward models even when the full physics is multi-physics**:

| Existing | Forward model in current manifest | What's missing for full multi-physics |
|---|---|---|
| L1-041 PAT | `p(r,t) = ∫ A(r') · envelope(t − \|r−r'\|/c) + n` (acoustic-only, A treated as input) | Joint optical absorption → thermoelastic → acoustic; recovers absorption coefficient `μ_a(r)` |
| L1-055 MRE | `φ = γ · G_MEG · ∫ u(t) dt; extract u(r,t) → stiffness via Helmholtz` (MR-phase + post-step Helmholtz) | Joint vibration source → tissue mechanics → MR phase; recovers full elasticity tensor with boundary coupling |
| L1-059 SWI | Magnitude × phase_mask^n (phase-weighted display only) | Full QSM with Maxwell magnetostatic dipole inversion |

These present **opportunities for v3 standalone Principles** with d_principle ≥ 0.30 from the existing entries (the joint physics has different fingerprint primitives).

### Multi-modal fusion (already covered)

The `O_multimodal_fusion/` subtree has 6 Principles for cross-modal fusion (PET-CT, PET-MR, SPECT-CT, US-MRI, CT-fluorescence, CLEM). These already include joint multi-modal physics — don't duplicate.

---

## The eight v3 standalone medical imaging candidates

For each: (a) clinical motivation, (b) joint forward model, (c) component physics, (d) L_DAG estimate, (e) joint W and C certificate references, (f) why it's distinct from existing genesis Principles.

### 1. Quantitative Susceptibility Mapping (QSM)

**Clinical motivation:** Recovers tissue magnetic susceptibility `χ(r)` — sensitive to iron deposition (Parkinson's, multiple sclerosis), calcification (tumors, vascular), demyelination (MS lesions), deep-brain-stimulation electrode targeting, and brain microbleeds. Routine clinical imaging at most academic medical centers.

**Joint forward model:**
```
B_z(r) - B_0 = (1/3) [3·d̂·d̂ᵀ - I] : (χ(r) ⊗ B_0)            (Maxwell magnetostatics)
              = D(r) ⊛ χ(r)                                    (dipole convolution kernel)

Phase φ(r) = γ · TE · [B_z(r) - B_0]                          (MR phase encoding)

Joint inverse: recover χ(r) from measured φ(r) given B_0, TE
```

**Components (single-physics):**
- MR phase encoding (existing L1-030 MRI, but used as a dependency, not a parent)
- Maxwell magnetostatic field perturbation (electromagnetic Principle in `agent-physics/U_electromagnetics/`)
- Dipole-kernel deconvolution (linear inverse problem in cosine-space with zero-cone artifacts)

**L_DAG estimate:** ~6-8, with `n_c = 2`:
- coupling 1: phase-to-field linear relationship (analytic, well-conditioned)
- coupling 2: field-to-susceptibility dipole convolution (ill-conditioned at magic angle; requires regularization)

**Joint W and C certificates:**
- W: well-posedness of MEDI / TKD / iLSQR formulations (Liu, de Rochefort, Wharton, Bilgic literature 2009-2018)
- C: standard Tikhonov / TV-regularized convergence with bounded condition number after wave-cone regularization

**Why distinct from L1-059 SWI:** SWI is phase-weighted display only — `Magnitude × phase_mask^n`. The forward model treats phase as the output. QSM treats phase as the *measurement* and inverts to susceptibility — entirely different `solution_space` (3D susceptibility vs 2D weighted image) and different primitives (adds Maxwell magnetostatics, dipole kernel). d_principle ≈ 0.5 from SWI — solidly "Distinct."

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-503_qsm.json`.

**Authoring effort:** ~5-7 days. Ample literature; well-established formulations.

---

### 2. Quantitative Photoacoustic Tomography (qPAT)

**Clinical motivation:** Recovers optical absorption coefficient `μ_a(r, λ)` at multiple wavelengths → blood oxygenation maps, hemoglobin concentration, contrast-agent uptake. Applications in oncology (tumor angiogenesis), vascular imaging, lymph-node mapping. UTSW has an active photoacoustic imaging program; broad clinical translation interest.

**Joint forward model:**
```
Φ(r, λ) = light fluence after diffusion through tissue           (radiative transfer)
       = ∫ G(r, r'; μ_a, μ_s', λ) · S(r') dr'                    (Green's-function fluence)

H(r, λ) = μ_a(r, λ) · Φ(r, λ)                                    (energy absorption — coupling)

p_0(r) = Γ · H(r, λ)                                             (thermoelastic source)

p(r, t) = ∫ Σ ∫ p_0(r') δ(t - |r - r'|/c) dr' dλ                 (acoustic propagation)

Joint inverse: recover μ_a(r, λ) from p(r, t) given μ_s'(r), Γ, c
```

**Components (single-physics):**
- Optical radiative transfer / diffusion equation (existing L1-040 DOT covers part; reused as dependency)
- Thermoelastic source generation (mechanics; small extension)
- Acoustic wave propagation (existing in `agent-physics/V_acoustics/`; reused as dependency)

**L_DAG estimate:** ~7-9, with `n_c = 2`:
- coupling 1: light-fluence → energy-absorption product (multiplicative, position-dependent)
- coupling 2: thermoelastic source → acoustic wave (causal time-domain coupling)

**Joint W and C certificates:**
- W: well-posedness of qPAT inverse problem in two-step (acoustic inversion → optical inversion) and one-step (joint) formulations (Bal, Uhlmann, Cox, Beard, Arridge literature 2007-2020)
- C: convergence of model-based iterative reconstruction with adjoint forward solvers; spatial resolution limited by acoustic bandwidth, spectral resolution by wavelength sampling

**Why distinct from L1-041 PAT:** L1-041 PAT's forward is `p(r,t) = ∫ A(r') · envelope(t − |r−r'|/c) + n` — treats optical-absorption-induced pressure A(r) as the *input* to the acoustic forward. qPAT explicitly adds the optical-fluence stage and recovers `μ_a(r, λ)` as the inversion target. Different `solution_space` (3D-spectral absorption vs 3D pressure), different primitives (adds optical diffusion). d_principle ≈ 0.42 from L1-041 — "Distinct" advisory threshold.

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-504_qpat.json`.

**Authoring effort:** ~6-8 days. Joint physics is well-established; numerous reference solvers (Cox/Beard k-Wave, Arridge Toast++).

---

### 3. Pharmacokinetic Dynamic PET (PK-PET)

**Clinical motivation:** Recovers tracer kinetic parameters (e.g., FDG metabolic rate `K_i`, FLT proliferation `K_1`, receptor binding `K_3/K_4`) by combining dynamic PET acquisition with compartmental ODE modeling. Standard for quantitative oncology imaging, neuroreceptor imaging, cardiac metabolism. Replaces semi-quantitative SUV with absolute kinetic rates.

**Joint forward model:**
```
dC_T/dt = K_1 · C_p(t) − k_2 · C_T − k_3 · C_T + k_4 · C_T_bound  (compartmental ODE)
dC_T_bound/dt = k_3 · C_T − k_4 · C_T_bound

A(r, t) = α(r) · [C_T(r, t) + C_T_bound(r, t)]                    (tissue activity = concentration × tracer-binding)

y(s, t) = ∫ A(r, t) · h_PET(s; r) dr + n(s, t)                    (PET projection forward)

Joint inverse: recover (K_1, k_2, k_3, k_4)(r) from y(s, t) given C_p(t)
```

**Components (single-physics):**
- PET projection physics (existing L1-033 PET; reused as dependency)
- Compartmental ODE kinetics (chemistry / kinetics primitive; small extension to genesis)
- Plasma input function `C_p(t)` (measured separately; calibration input)

**L_DAG estimate:** ~6-8, with `n_c = 2`:
- coupling 1: ODE kinetics state → tissue activity (deterministic)
- coupling 2: time-resolved activity → time-resolved projection (linear, time-coupled)

**Joint W and C certificates:**
- W: identifiability of kinetic parameters under standard inputs (Carson, Gunn, Innis 1996-2007 reviews)
- C: convergence of iterative kinetic reconstruction (4D-EM-ML, direct kinetic ML, NN-prior); error bounds tied to noise equivalent count rate

**Why distinct from L1-033 PET:** L1-033 PET is a single-time-frame projection inversion recovering activity distribution `A(r)`. PK-PET adds the temporal kinetics dimension and recovers physiological rate constants. Different `solution_space` (kinetic parameter map vs activity map), different primitives (adds ODE solver), different output dimensionality. d_principle ≈ 0.55 from L1-033 — "Distinct."

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-505_pkpet.json`.

**Authoring effort:** ~5-7 days. Standard kinetic models; mature reconstruction theory.

---

### 4. Hyperpolarized 13C Metabolic MRI

**Clinical motivation:** Real-time imaging of metabolic conversion (e.g., pyruvate → lactate in cancer; pyruvate → bicarbonate in heart; alanine in liver). Hyperpolarization via dynamic nuclear polarization (DNP) yields >10,000× MR signal enhancement, enabling kinetic imaging of injected metabolites. Active translational research at UTSW, UCSF, Cambridge, Sloan Kettering.

**Joint forward model:**
```
dM_pyr/dt = -k_PL · M_pyr - k_PA · M_pyr - 1/T1_pyr · M_pyr + R_pyr(t)    (chemical exchange)
dM_lac/dt = +k_PL · M_pyr - 1/T1_lac · M_lac
dM_ala/dt = +k_PA · M_pyr - 1/T1_ala · M_ala

Each metabolite acquired at distinct chemical shift:
S_m(k, t) = ∫ M_m(r, t) · exp(-i·2π·k·r) · exp(-i·ω_m·TE) · sinc(...) dr
                                                          (chemical-shift-resolved MR encoding)

Joint inverse: recover (k_PL, k_PA, T1_pyr, T1_lac, T1_ala)(r)
              from {S_pyr(k,t), S_lac(k,t), S_ala(k,t)} given injection bolus
```

**Components (single-physics):**
- DNP polarization transfer (specialized DNP physics; small new primitive)
- Chemical-exchange ODE kinetics (chemistry primitive)
- Spectrally-resolved MR encoding (existing L1-030 MRI + L1-044 MRS; reused)

**L_DAG estimate:** ~8-10, with `n_c = 3`:
- coupling 1: DNP polarization → metabolite signal magnitude
- coupling 2: chemical-exchange → multi-pool MR signal
- coupling 3: T1 relaxation → time-decay of all signals

**Joint W and C certificates:**
- W: identifiability of metabolic rate constants from chemical-shift-resolved time-series (Bahrami, Larson, Vigneron literature 2013-2020)
- C: convergence of joint kinetic + spatial reconstruction; resolution limited by hyperpolarization decay window (~60-120 s)

**Why distinct from L1-044 MRS and L1-030 MRI:** L1-044 MRS is steady-state spectroscopy; doesn't model kinetics or hyperpolarization. L1-030 MRI is single-frequency; doesn't model chemical-shift-resolved dynamics. HP-13C combines DNP physics + ODE kinetics + chemical-shift MR — d_principle ≈ 0.6 from both — "Distinct."

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-506_hp13c_mri.json`.

**Authoring effort:** ~7-10 days. Cutting-edge but well-documented in 2015-2024 literature; reference reconstruction code (HypMet, PyHP) available.

---

### 5. Joint MEG-EEG Source Imaging

**Clinical motivation:** Recovers neural source activity `J(r, t)` by jointly inverting magnetoencephalography (MEG) and electroencephalography (EEG) measurements. Combined modalities outperform either alone — MEG is sensitive to tangential sources, EEG to radial; together they triangulate. Clinical use in epilepsy presurgical mapping, brain-computer interfaces, evoked-response studies. Strong UTSW + UT Dallas neuroscience collaboration potential.

**Joint forward model:**
```
B(r_sensor, t) = ∫ G_M(r_sensor, r') · J(r', t) dr'    (MEG: Maxwell magnetostatic Biot-Savart)
V(r_electrode, t) = ∫ G_E(r_electrode, r') · J(r', t) dr'    (EEG: Poisson electrostatic in head model)

Joint measurement: y(t) = [B; V](t) = [G_M; G_E] · J(t) + n(t)

Joint inverse: recover J(r, t) from y(t) given head conductivity model
```

**Components (single-physics):**
- MEG forward (existing L1-067 MEG; reused as dependency)
- EEG forward (existing L1-068 EEG; reused as dependency)
- Head-volume-conductor model (anatomical MR-derived; cross-input)

**L_DAG estimate:** ~7-9, with `n_c = 2`:
- coupling 1: same neural source seen by both MEG and EEG sensors (joint observation)
- coupling 2: shared head-conductivity model parameterizes both forwards

**Joint W and C certificates:**
- W: improved well-posedness of joint MEG+EEG inverse vs either alone (Mosher, Huang, Wood literature 1999-2018)
- C: convergence of MNE / sLORETA / beamformer / dynamic causal modeling joint inversions

**Why distinct from L1-067 (MEG alone) and L1-068 (EEG alone):** L1-067 inverts only `B`; L1-068 inverts only `V`. Joint MEG-EEG inverts `[B; V]` simultaneously with shared head model. Different `solution_space` (improved-resolution joint source) and different primitives (adds Poisson electrostatic alongside Biot-Savart). d_principle ≈ 0.5 from each parent — "Distinct."

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-507_meg_eeg_joint.json`.

**Authoring effort:** ~5-7 days. Mature theory; reference implementations in Brainstorm, MNE-Python, FieldTrip.

---

### 6. Optical Coherence Elastography (OCE)

**Clinical motivation:** Recovers tissue mechanical properties (Young's modulus, shear modulus) at micrometer resolution by tracking sub-resolution displacements in OCT signal under applied loading. Emerging in ophthalmology (corneal biomechanics), dermatology (skin cancer staging), oncology (small-tumor stiffness mapping). Could pair with the v2 PWDR PillCam-SPECTRA Principle for endoscopic stiffness measurement.

**Joint forward model:**
```
I(r, t) = OCT_forward(scattering profile R(r, t))                  (OCT signal acquisition)

R(r, t) = R(r - u(r, t))                                           (displacement-shifted scatter)

∂_tt u = (1/ρ) ∇·σ(u, μ, λ)                                        (linear elasticity wave)
σ = 2μ·∇^s u + λ·(∇·u)·I                                          (constitutive law)

Joint inverse: recover (μ, λ)(r) from I(r, t) given applied loading boundary conditions
```

**Components (single-physics):**
- OCT signal acquisition (existing L1-042 OCT; reused as dependency)
- Linear elasticity wave propagation (existing L1-207 linear_elasticity; reused as dependency)
- Lagrangian-to-Eulerian displacement coupling

**L_DAG estimate:** ~6-8, with `n_c = 2`.

**Subdomain:** `C_medical_imaging/`. L1 ID candidate: `L1-508_oce.json`. Authoring effort: ~5-6 days.

---

### 7. Photoacoustic-Ultrasound Dual-Mode (PAUS)

**Clinical motivation:** Same probe, same scan, dual contrast — PA for functional/molecular (chromophore concentration), US for anatomical/morphological (tissue echogenicity). Commercial systems (Verasonics, FUJIFILM-VisualSonics) combine both in real-time. Used in breast imaging, vascular imaging, small-animal preclinical.

**Joint forward model:**
```
y_PA(s, t) = PA_forward(μ_a, μ_s', tissue map)        (light → pressure, qPAT-style)
y_US(s, t) = US_forward(impedance map, tissue map)    (acoustic Born / pulse-echo)

Joint inverse: recover (μ_a, impedance, tissue) from (y_PA, y_US)
```

**Components (single-physics):**
- qPAT (proposed candidate #2 above, if authored)
- Ultrasound (existing L1-032 ultrasound; reused as dependency)

**L_DAG estimate:** ~7-9, with `n_c = 2`. Authoring effort: ~5-7 days.

---

### 8. Cardiac 4D-Flow MRI with Hemodynamic Biomechanics

**Clinical motivation:** Recovers blood velocity field `v(r, t)` AND vessel-wall pressure `p(r, t)` AND tissue stiffness in cardiac chambers. Diagnostic for valvular heart disease, congenital heart disease, aortic dissection, stenosis. Combines 4D phase-contrast MR acquisition with constraint-aware Navier-Stokes regularization.

**Joint forward model:**
```
∂_t v + (v·∇) v = -1/ρ ∇p + ν ∇²v + f                   (Navier-Stokes in chamber)
∇·v = 0                                                  (incompressibility)

φ_PC(r, t) = γ · TE · venc · v(r, t)                     (phase-contrast MR encoding)

Joint inverse: recover (v, p)(r, t) from φ_PC(r, t) under NS constraint
```

**Components (single-physics):**
- 4D phase-contrast MR (existing L1-030 MRI; specialized PC encoding)
- Navier-Stokes (existing L1-170 incompressible_ns; reused)

**L_DAG estimate:** ~7-9, with `n_c = 2`. Authoring effort: ~6-8 days.

---

## Director's Path A pick recommendation: 2 Principles

For Path A (1-2 weeks, Director-authored), the strongest pair is:

### Pick 1: **Quantitative Susceptibility Mapping (QSM)** — `L1-503_qsm.json`

- Clinically deployed at most academic medical centers; broad familiarity
- Joint physics math is mature (Liu et al. MEDI; de Rochefort et al. STI; Wharton et al. iLSQR)
- L_DAG ≈ 6-8 — moderate complexity
- Components (MR phase + magnetostatic) already have analogues in genesis — easy to cite as `related_principles`
- Distinct from L1-059 SWI by d_principle ≈ 0.5 — solid "Distinct" advisory
- Authoring time: ~5-7 days
- Strong UTSW relevance — QSM is commonly read at neuroradiology

### Pick 2: **Quantitative Photoacoustic Tomography (qPAT)** — `L1-504_qpat.json`

- Active research at UTSW imaging labs; high translational potential
- THE textbook example of multi-physics medical imaging (optical + thermoelastic + acoustic)
- L_DAG ≈ 7-9 — substantial multi-physics
- Distinct from L1-041 PAT (acoustic-only) by d_principle ≈ 0.42 — "Distinct"
- Authoring time: ~6-8 days
- Aligns with PWM's existing imaging emphasis — natural fit for genesis

These two together cover both clinical-deployed (QSM) and emerging-research (qPAT) ends of the medical multi-physics spectrum, span both MR and optical/acoustic carriers, and are authoring-feasible by Director within the Path A window.

### If extending to Path B (2 more)

Add: **Pharmacokinetic Dynamic PET (PK-PET)** — `L1-505_pkpet.json` and **Hyperpolarized 13C MRI** — `L1-506_hp13c_mri.json`. Both extend the PET and MR modalities respectively into kinetics-aware quantitative imaging — high research value, broad clinical interest.

### If extending to Path C (full set)

Add: **Joint MEG-EEG** — `L1-507`, **OCE** — `L1-508`, **PAUS** — `L1-509`, **Cardiac 4D-flow with biomechanics** — `L1-510`.

Final genesis count under each path:

| Path | New medical imaging v3 Principles | Total genesis size |
|---|---|---|
| A | 2 (QSM + qPAT) | 504 |
| B | 4 (A + PK-PET + HP-13C) | 506 |
| C | 8 (B + MEG-EEG + OCE + PAUS + 4D-flow) | 510 |

Plus parallel batches:
- 10-15 v2 PWDR exemplars from `PWM_V2_GENESIS_INCLUSION.md` → adds another 10-15
- 4 missing analytical components from `PWM_V3_COMPOSITES_AND_GENESIS_COMPONENTS.md` → adds 4

**Path C combined with v2 batch + missing components ≈ 526 total genesis Principles.** Strong "PWM is a multi-modality, multi-physics medical-imaging-anchored protocol" identity at deploy.

---

## Why these are not "just renaming" existing genesis Principles

Reviewer concern: "Aren't QSM and qPAT just SWI and PAT with different forward operators?" The d_principle distance metric flags whether two Principles are too similar. For each of the proposed candidates:

| Candidate | Closest existing genesis | d_principle estimate | Decision |
|---|---|---|---|
| QSM (`L1-503`) | L1-059 SWI | ~0.5 | Distinct |
| qPAT (`L1-504`) | L1-041 PAT | ~0.42 | Distinct |
| PK-PET (`L1-505`) | L1-033 PET | ~0.55 | Distinct |
| HP-13C (`L1-506`) | L1-044 MRS | ~0.6 | Distinct |
| Joint MEG-EEG (`L1-507`) | L1-067 MEG | ~0.5 | Distinct |
| OCE (`L1-508`) | L1-042 OCT + L1-047 elastography | ~0.45 | Distinct |
| PAUS (`L1-509`) | L1-041 PAT + L1-032 US | ~0.4 | Distinct |
| Cardiac 4D-flow (`L1-510`) | L1-058 MRA | ~0.5 | Distinct |

All eight pass the v1 d_principle ≥ 0.30 advisory threshold for separate-Principle staking. Each adds genuinely new physics primitives (Maxwell magnetostatics for QSM; thermoelastic source for qPAT; ODE kinetics for PK-PET; DNP + chemical exchange for HP-13C; etc.).

---

## Practical execution

### For each picked candidate

- [ ] Director picks 2-5 from the list above
- [ ] For each pick, draft the manifest JSON following the schema of existing analytical L1 manifests
  - `gate_class: "analytical"` (the standalone form per `PWM_V3_STANDALONE_VS_COMPOSITE.md`)
  - L_DAG breakdown with explicit `n_c` value
  - Joint W and C certificates with literature citations
  - `related_principles: [L1-XXX, L1-YYY, ...]` informational field listing components
  - `physics_fingerprint` block with full primitive set
  - `spec_range` block declaring which Ω-tier specs earn A_k + T_k
- [ ] Run validation: P1-P10 + S1-S4 + d_principle distance check (must be ≥ 0.30 from all existing genesis)
- [ ] Place in `pwm-team/content/agent-imaging/principles/C_medical_imaging/` with next available L1 IDs (L1-503, L1-504, ...)
- [ ] Add path to `register_genesis.js` registration list
- [ ] Sepolia dry-run

### Director-authored vs Reserve grant

- **QSM**: Director-authored (5-7 days). Director's UTSW imaging context covers neuroradiology QSM use; mature literature.
- **qPAT**: Director-authored (6-8 days). Photoacoustic imaging is an active UTSW research area.
- **PK-PET**: Director or contracted UTSW nuclear-medicine collaborator (~$3-5K Reserve grant if external).
- **HP-13C MRI**: Likely contracted to a specialist (UCSF, UTSW, Cambridge) — niche expertise needed (~$5-8K Reserve grant).
- **MEG-EEG joint**: Either Director or contracted (UT Dallas neuroscience collaboration potential).
- **OCE / PAUS / 4D-flow**: Reserve grants to specialist labs (~$3-6K each).

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked for medical imaging v3 standalone candidates. Audited current 142 genesis imaging Principles + 6 multimodal-fusion Principles. Identified 8 clean candidates with d_principle ≥ 0.42 from existing entries. Recommended Path A pick: QSM + qPAT. |
| _TBD_ | Director picks 2-5 from the candidate list. |
| _TBD_ | First standalone v3 medical imaging manifest (likely `L1-503_qsm.json`) drafted. |
| _TBD_ | Validation against P1-P10 + S1-S4 + d_principle. |
| _TBD_ | Path-specific manifests batch-validated, committed, registered. |
| _TBD_ | Mainnet deploy at Step 7 with the expanded medical imaging genesis batch. |

---

## Summary table

| Question | Answer |
|---|---|
| Are there v3-eligible multi-physics medical imaging methods missing from current genesis? | **Yes — 8 strong candidates** (QSM, qPAT, PK-PET, HP-13C MRI, joint MEG-EEG, OCE, PAUS, cardiac 4D-flow with biomechanics). |
| Why are these v3-eligible? | Each has a joint coupled forward model with `n_c > 0` coupling constraints, recovers a fundamentally different inversion target than its single-physics cousin, and passes d_principle ≥ 0.30 distinctness. |
| Director's recommended Path A pair? | **QSM + qPAT.** Both clinically/research-relevant, both moderate L_DAG, both authoring-feasible in 1-2 weeks. |
| Total v3 medical imaging if Path C executed? | 8 new entries → genesis count 510 just from medical-imaging v3 (before v2 batch + missing components). |
| Is this consistent with the standalone-as-default design? | **Yes.** Each registers as v1-analytical with `gate_class: "analytical"`, `n_c > 0`, full single-creator L1 royalty. No multi-parent composite needed. |
| Cost? | Path A: Director-authored, ~$0. Path B/C: ~$10-25K Reserve grants. Zero contract changes. |
| Next action? | Director picks 2-5 from the list. Claude can draft the first manifest (likely `L1-503_qsm.json`) in the next session. |

The v3 standalone medical imaging genesis batch is ready to author. Director picks the count and the manifest authoring begins.
