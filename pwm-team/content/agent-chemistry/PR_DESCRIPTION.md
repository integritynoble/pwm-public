# agent-chemistry: genesis principles (64 / 64) — feat/genesis-principles-chemistry

## Summary

All five chemistry domain clusters complete. **64 principles × 3 layers = 192 JSONs.**

| Domain | Source folder | Count |
|---|---|---|
| Computational chemistry | `X_comp_chemistry/` | 18 |
| Quantum mechanics | `Y_quantum_mechanics/` | 15 |
| Materials science | `Z_materials_science/` | 15 |
| Polymer physics | `AL_polymer_physics/` | 6 |
| Semiconductor physics | `AN_semiconductor/` | 10 |

## Difficulty distribution

| δ | Tier | Count |
|---|---|---|
| 1 | trivial | 1 (Michaelis-Menten) |
| 3 | standard | 24 |
| 5 | challenging | 30 |
| 10 | hard | 9 |
| 50 | frontier | 0 |

## Hard (δ=10) principles — flagged for reviewer attention

These are the non-trivial, many-body / stochastic methods whose forward models are genuinely hard and whose parameter inversions are known ill-posed. Please double-check the P = (E, G, W, C) quadruples and hardness_rule_check on these:

- **X_comp_chemistry/296** Post-Hartree-Fock (MP2, CCSD(T))
- **X_comp_chemistry/298** Ab Initio MD (Car-Parrinello / BOMD)
- **Y_quantum_mechanics/319** GW Approximation
- **Y_quantum_mechanics/320** Bethe-Salpeter Equation
- **Y_quantum_mechanics/321** Quantum Monte Carlo (VMC + DMC)
- **Y_quantum_mechanics/322** DMRG
- **Y_quantum_mechanics/325** Electron-Phonon Coupling (Eliashberg)
- **AN_semiconductor/491** NEGF Quantum Transport
- **Z_materials_science/338** Radiation Damage Cascade Dynamics

No frontier (δ=50) principles in this batch.

## Quality checks passed

- [x] 192/192 JSONs validate (schema + cross-layer: L1 `forward_model` == L2 `six_tuple.E.forward`)
- [x] All 7 `physics_fingerprint` fields present on every L1
- [x] Every L2 has `epsilon_fn` as a string expression; all 64 evaluate cleanly over 10 random Ω samples (S4)
- [x] Every L3 has 4 tiers (T1–T4) with `d_ibench` ≥ 0.10 and ≥10% spacing in ≥1 Ω dim
- [x] Hardness rule: top baseline fails at T4 in all 64 benchmarks (fixed 4 after initial audit)
- [x] Every L3 has `anti_overfitting_mechanisms` block (M1–M6)
- [x] Chemistry-appropriate `error_metric` — 50+ distinct labels (`energy_error_eV/mHa`, `MAE_kcal_mol`, `RMSE_angstrom`, `band_gap_error_eV`, `DG_solv_kcal_mol`, `Tc_relative_error`, `kappa_relative_error`, `V_cell_L2_mV`, `i_corr_log_error`, etc.)
- [x] `physics_fingerprint.carrier` spans electron / photon / phonon / ion / none (classical)

## Source-data note (important)

All 64 source `.md` files under `content/agent-chemistry/source/*/` are the widefield-fluorescence template (genesis fan-out artifact, flagged in coord log update 8). Every JSON carries a `source_data_quality_note` documenting this. **Physics content is grounded in canonical domain literature** — Groot-Warren (DPD), Doi-Edwards (reptation), Kohn-Sham (DFT), Eliashberg (e-ph), GW100 benchmark, QM9, GMTKN55, FreeSolv, Materials Project, NIST Kinetics, etc. — not the template text.

## Test plan

- [ ] Reviewer spot-checks 2–3 δ=10 principles for physical correctness of `E.forward_model`, `G.dag`, and W/C certificates
- [ ] CI re-runs the schema + hardness + epsilon_fn audits on the four fix commits
- [ ] Dataset references (QM9, GMTKN55, Materials Project, etc.) confirmed resolvable by agent-scoring's later P-benchmark harness

## Commits on this branch

1. `6e17a56` feat(chemistry): 64 genesis principles (192 JSONs)
2. `a3f5763` chore(coord): signal `agent-chemistry = PR_READY`
3. `9d3552a` fix(chemistry): bump T4 baselines on 4 L3 JSONs (hardness rule)
4. `a4080f1` fix(chemistry): L2-479 epsilon_fn variable name

Closes the agent-chemistry row in the Content Track board. Signal `agent-chemistry = PR_OPEN` should flip in `progress.md` once this PR is open.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
