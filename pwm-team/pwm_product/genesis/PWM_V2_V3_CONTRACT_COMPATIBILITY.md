# Can the current PWM protocol support v2 and v3 specs in the future?

**Date:** 2026-04-29
**Owner:** Director
**Audience:** PWM contract authors, deploy planners, governance reviewers
**Status:** standalone Q&A — captures the compatibility analysis between the v1 contracts and the proposed v2 / v3 specs
**Cross-references:**
- `papers/Proof-of-Solution/pwm_overview1.md` — the spec the v1 contracts implement
- `papers/Proof-of-Solution/pwm_overview2.md` — proposed v2 spec, Appendix C is the canonical evolvability source
- `papers/Proof-of-Solution/pwm_overview3.md` — proposed v3 spec, Appendix C is the canonical evolvability source
- `pwm-team/pwm_product/genesis/PWM_GATE_CLASSES_AND_SCALING.md` — design rationale for v2 / v3
- `pwm-team/infrastructure/agent-contracts/contracts/*.sol` — the seven v1 contracts

---

## TL;DR

| Version | Can current contracts support it? | What's needed |
|---|---|---|
| **v2** | **Mostly yes** (~70%) | One mandatory add-on contract + one optional sibling registry + an off-chain settlement service. **No replacement of v1 contracts.** |
| **v3** | **Not as-is** (~40%) | A planned **V2 contract suite** (`PWMRegistryV2` + `PWMGovernanceV2` + `PWMRewardV2`) deployed alongside v1. **L1-L4 mining keeps flowing through v1.** |

The v1 contracts were authored against `pwm_overview1.md` and are immutable once deployed (no proxy, no upgrade pattern, no admin-mutable logic beyond parameter setters in `PWMGovernance`). Anything v2 or v3 adds therefore ships as **additive contracts deployed alongside v1**, never as replacements.

---

## Why the question is non-trivial

PWM v1 contracts (the seven `.sol` files in `pwm-team/infrastructure/agent-contracts/contracts/`) made deliberate immutability choices:

1. `PWMRegistry.register` hardcodes `layer >= 1 && layer <= 4` (revert otherwise).
2. `PWMRegistry.Artifact.parentHash` is `bytes32` — a single parent.
3. `PWMReward` distribution percentages (Rank1=40%, AC 55%, CP 55%, etc.) are baked in.
4. `PWMGovernance` is a flat 3-of-5 multisig; the only structural transition is the one-way `activateDAO()` switch to contribution-weighted voting.
5. None of the seven contracts has an upgrade pattern or proxy.

These were the right choices for v1 — they make the protocol genuinely trustless. But they mean **v2 and v3 cannot mutate v1 in place**. They must extend by adding new contracts.

---

## v2 compatibility (detailed)

Mapping every v2 feature against the v1 contract surface:

| v2 § | Feature | v1 contract impact | Add-on needed? |
|---|---|---|---|
| § 2 | `gate_class` field on L1 manifest | None — manifest is off-chain; only the hash hits `PWMCertificate.submit` | **No** |
| § 3 | `L0_meta` artifact type | `PWMRegistry.register` reverts on layer ∉ {1,2,3,4} → cannot register `L0_meta` directly | **Yes — `PWML0MetaRegistry`** (sibling to `PWMRegistry`) |
| § 4 | Discrete-output gate substitutions (κ → Δ, h → 1/√n, etc.) | None — pure off-chain manifest content | **No** |
| § 5 | Option-3 recast canonical pattern | None — review-time guidance | **No** |
| § 6 | Reward differentiation 1.0 / 1.0 / 0.5 | `PWMReward` has fixed splits; no per-cert multiplier hook | **Yes** — either off-chain settlement service (preferred) or parallel `PWMRewardV2` |
| § 7 | Reviewer checklist | None — off-chain governance process | **No** |
| § 8 | Distance-metric extension | None — off-chain matcher logic | **No** |
| § 9 | Manifest schema diff | None — off-chain JSON schema | **No** |
| § 10 | Migration of 400 imaging Principles | None — manifests get a `gate_class: "analytical"` line, hash unchanged in spirit | **No** |

**Net: 1 mandatory add-on contract, 1 optional sibling, 1 off-chain service.** Roughly 70% of v2 is pure off-chain work.

### v2 add-on contract: `PWMGateClassRegistry`

The single mandatory new contract. Maps `certHash → gate_class` so off-chain matchers, reward calculators, and the v3 auto-verifier have an on-chain source of truth.

```solidity
contract PWMGateClassRegistry {
    enum GateClass { Unset, Analytical, PhysicalWithDiscreteReadout, DataDrivenStatistical }
    mapping(bytes32 => GateClass) public gateClassOf;
    mapping(bytes32 => bytes32)   public l0MetaParent;
    address public governance;   // == PWMGovernance; only it writes
    function setGateClass(bytes32 certHash, GateClass class, bytes32 l0Meta) external;
}
```

Write access is gated by `PWMGovernance`'s 3-of-5 multisig with the existing 48h time-lock.

### v2 reward multiplier: off-chain settlement (preferred)

`PWMReward` keeps computing the rank-based draw exactly as v1 defines. An off-chain settlement service reads `gate_class` from `PWMGateClassRegistry` and applies the multiplier; pays out via a daily batch transaction signed by `PWMGovernance`.

```
v1 PWMReward → raw_payout(certHash)
       ↓
off-chain service reads PWMGateClassRegistry
       ↓
final_payout = raw_payout × multiplier(gate_class)
       ↓
PWMGovernance batch-signs the ERC-20 transfer
```

The 50% withheld from `data_driven_statistical` rewards routes back into `PWMTreasury` for the originating Principle — or into a v2-specific recast-incentive pool.

### v2 cost estimate

| Item | Effort |
|---|---|
| `PWMGateClassRegistry` (write + tests + audit) | ~1.5 weeks engineer + ~$5K audit |
| `PWML0MetaRegistry` (write + tests + audit) | ~1 week engineer + ~$3K audit |
| Off-chain settlement service | ~3 weeks engineer + ~$15K audit |
| Backfill batch + addresses.json + client release | ~1 week engineer |
| **Total** | **~6.5 weeks engineer + ~$23K audit** |

About 10% of the v1 deploy effort. v2 is genuinely cheap to ship.

### What v2 cannot enforce against v1 contracts

- **Hash-time enforcement.** v1 `PWMCertificate.submit` does not check that a `gate_class` exists in the side registry. Mitigation: governance refuses to seed a benchmark pool until the gate-class entry is present.
- **On-chain verification of statistical bounds.** S2*/S3*/S4* (VC, PAC-Bayes, conformal) cannot be checked by v1 contracts. They are checked by the v3 auto-verifier and committed via hash, not interpreted on-chain.

---

## v3 compatibility (detailed)

Mapping every v3 feature against the v1 contract surface:

| v3 § | Feature | v1 contract impact | Path |
|---|---|---|---|
| § 2.2 | DOMAIN / SUB_DOMAIN artifacts | `PWMRegistry.register` reverts on layer ∉ {1,2,3,4} — **cannot register new top-level types** | Needs `PWMRegistryV2` |
| § 2.3 | Per-domain reviewer committees | `PWMGovernance` is a flat 3-of-5 multisig; `activateDAO()` is one-way to contribution-weighted voting, not committee partitioning | Needs `PWMGovernanceV2` |
| § 3 | Auto-verifier service | Off-chain; output hashed into manifest | No contract change |
| § 3.4 | Auto-verifier as on-chain artifact | New artifact kind | Reuses `PWMRegistryV2` |
| § 4 | AI authoring agents | Just submitter addresses; reputation off-chain | No contract change |
| § 4.3 | AUTHORING_AGENT artifact | New artifact kind | Reuses `PWMRegistryV2` |
| § 5 | Composite Principles (multi-parent) | `Artifact.parentHash` is `bytes32`, not `bytes32[]` — **hard schema constraint** | Needs `PWMRegistryV2` |
| § 5.3 | Composition reward formula | `PWMReward` has fixed splits with single AC / CP attribution; no multi-component royalty propagation | Needs `PWMRewardV2` (composite-only) |
| § 6 | Domain SLA + reviewer-load model | Pure off-chain governance | No contract change |

Three of five new artifact types and one core governance change require new contracts.

### The v3 V2 contract suite

v3 introduces **three new contracts**, all deployed alongside v1 (never replacing it):

#### `PWMRegistryV2`

```solidity
contract PWMRegistryV2 {
    enum ArtifactKind {
        Unset,
        Domain,            // v3 § 2.2
        SubDomain,         // v3 § 2.2
        L0Meta,            // v2 § 3
        L1Composite,       // v3 § 5
        AutoVerifier,      // v3 § 3.4
        AuthoringAgent     // v3 § 4.3
    }
    struct Artifact {
        ArtifactKind kind;
        bytes32[]    parents;     // multi-parent for composites
        address      creator;
        uint256      timestamp;
        bytes32      contentHash;
    }
    mapping(bytes32 => Artifact) private _artifacts;
    address public immutable v1Registry;   // pinned for cross-reference
    function register(bytes32 hash, ArtifactKind kind, bytes32[] calldata parents,
                      bytes32 contentHash, address creator) external;
}
```

**Critical:** L1-L4 keep flowing through v1 `PWMRegistry`. Nothing in the L4 mining path moves to V2. V2 holds a read-only address pin to v1 so any composite's components can be resolved through one canonical entry point.

#### `PWMGovernanceV2`

```solidity
contract PWMGovernanceV2 {
    struct Committee {
        bytes32   domainHash;
        address[] members;     // 5 members
        uint8     quorum;      // 3 of 5
    }
    mapping(bytes32 => Committee) public committeeOf;
    address public v1Governance;   // PWMGovernance — still owns protocol parameters
    function appointCommittee(bytes32 domainHash, address[] calldata members) external;
    function approveSubmission(bytes32 domainHash, bytes32 certHash, bytes calldata sigs) external;
}
```

v1 `PWMGovernance` continues to own protocol-wide parameters (`usdFloors`, `challengePeriods`, `slashingRates`, the v2 reward multiplier, `activateDAO()`). V2 governance handles per-domain reviewer committees only.

#### `PWMRewardV2` (composites only)

```solidity
contract PWMRewardV2 {
    address public immutable v1Reward;     // PWMReward; consulted for the base draw
    address public immutable gateClass;    // PWMGateClassRegistry from v2
    address public immutable registryV2;   // PWMRegistryV2
    function distributeComposite(bytes32 compositeCertHash) external;
}
```

Logic: resolve composite from `PWMRegistryV2` → pull `parents[]` and weights → compute base draw via v1 `PWMReward` → apply gate-class multiplier (weakest-link per v3 § 5.2) → distribute parent share + per-component shares.

Non-composite Principles **never touch this contract** — they continue to flow through v1 `PWMReward`.

### v3 cost estimate

| Item | Effort |
|---|---|
| `PWMRegistryV2` | ~3 weeks engineer + ~$15K audit |
| `PWMGovernanceV2` | ~3 weeks engineer + ~$15K audit |
| `PWMRewardV2` (composites) | ~2 weeks engineer + ~$10K audit |
| Genesis hierarchy backfill | ~1 week engineer |
| Auto-verifier v1.0 build + audit | ~6 weeks engineer + ~$20K audit |
| AI-authoring agent registration + reputation | ~3 weeks engineer |
| Client release (`pwm-node` v3-aware) | ~2 weeks engineer |
| **Total** | **~20 weeks engineer + ~$60K audit** |

About 30% of the v1 deploy effort. The auto-verifier dominates.

### v1 ↔ V2 read-bridging

To keep legacy clients functional during v3 rollout, two conventions:

1. **V2 artifacts surface as virtual layer-5+ entries** when read by v1-aware clients. A `pwm-node` v0.x client doesn't see V2's hierarchy but can still mine L4 against v1's L1 entries — smooth-upgrade path.
2. **L1_COMPOSITE entries register a stub in v1 `PWMRegistry`** as a layer-1 artifact (with `parentHash = bytes32(0)`) so v1 clients see the composite exists. The V2 entry is canonical for multi-parent structure; the v1 stub is for legacy discovery.

### What v3 cannot enforce against v1 contracts

- **Hierarchy validation.** v1 `PWMRegistry` accepts L1 entries lacking DOMAIN/SUB_DOMAIN. v3 enforces this at the `pwm-node` CLI submission layer; on-chain enforcement is economic (governance refuses to seed pools for naked L1s).
- **Auto-verifier as a precondition.** v1 `PWMCertificate.submit` does not call out to V2. The auto-verifier's PASS hash is committed in the manifest and verified by reviewers off-chain.
- **Composite payouts using v1-only components.** A composite referencing a v1 L1 (no `gate_class`) defaults to `data_driven_statistical` for the weakest-link calculation — deliberate safety bias.

---

## Why a clean parallel deploy beats retrofit

Three reasons, in order of importance:

1. **v1 contracts are immutable by design.** No upgrade pattern. Retrofit requires either replacing v1 (loses genesis hash provenance and testnet history) or pretending v3 features fit into v1 schemas (multi-parent and `ArtifactKind` are hard schema changes — they don't fit).
2. **Provenance integrity.** The 400 imaging Principles' v1 hashes anchor real on-chain history. Migrating them into a different schema would either invalidate that history or require dual-writing — both worse than keeping v1 canonical for L1-L4 and adding V2 alongside for v3-specific structure.
3. **Audit cost is bounded.** Three small additive contracts cost ~$40K in audits. Rewriting v1 would cost more than the original $50K-$100K v1 audit because the contracts are now load-bearing for real assets. **Additive contracts are cheaper to certify than modified contracts.**

The cost of additive complexity (two registries to query instead of one, two governance contracts to track) is real but bounded. It's the right trade-off given v1's immutability guarantees.

---

## Deploy sequencing recommendation

### Phase 1 — v1 mainnet (current focus)

Ship v1 to Base mainnet exactly as designed. No v2 / v3 features. The `gate_class` field can be added to manifests in the JSON schema layer with a default value of `analytical` so v2-aware clients can treat older entries consistently — but the v1 contracts don't read it.

### Phase 2 — v2 add-on (when first ~10 non-imaging Principles want to stake)

Trigger: first contributor wants to stake a `physical_with_discrete_readout` Principle (likely PillCam-SPECTRA per `CLASSIFICATION_SEGMENTATION_PRINCIPLES.md`).

Steps:
1. Author + audit `PWMGateClassRegistry`.
2. Author + audit `PWML0MetaRegistry`.
3. Stage to Sepolia; verify governance can write.
4. Backfill the existing imaging Principles' gate-class entries (`Analytical`) via a single multisig batch.
5. Author + audit the off-chain settlement service.
6. Deploy add-on registries to Base mainnet alongside v1.
7. Cut `pwm-node` v0.X release with v2 awareness.

**v1 contracts are not touched.**

### Phase 3 — v3 V2 suite (when catalog approaches ~1000 Principles)

Trigger: reviewer load on a flat catalog becomes the bottleneck; first multi-domain composite Principle is requested.

Steps:
1. Author + audit `PWMRegistryV2`.
2. Author + audit `PWMGovernanceV2`.
3. Author + audit `PWMRewardV2` (composites only).
4. Stage to Sepolia; end-to-end synthetic composite test.
5. Backfill genesis hierarchy (~12 DOMAIN, ~80 SUB_DOMAIN artifacts).
6. Backfill v2-era L1 Principles with (DOMAIN, SUB_DOMAIN) assignments in V2.
7. Deploy auto-verifier v1.0; register its hash as `AutoVerifier` artifact.
8. Open AI-authoring registration.
9. Deploy V2 suite to Base mainnet.

**v1 contracts are still not touched.** L1-L4 mining continues through v1.

---

## Open questions for governance

1. **v2 multiplier value (0.50 for `data_driven_statistical`).** Should it be 0.4 (push harder toward recasts) or 0.6 (admit more long-tail Principles)? Decide after first ~20 statistical Principles observed.
2. **v2 reward routing.** When the 50% multiplier withholds reward from a `data_driven_statistical` payout, where does the withheld amount go? Options: (a) back into `PWMTreasury` for the originating Principle; (b) into a v2-specific recast-incentive pool; (c) burned. Recommendation: (a) for simplicity.
3. **v3 domain count.** ~12 domains is a starting point. Recommend founders + first 50 stakers vote on the initial set.
4. **v3 cross-chain registry.** As PWM expands beyond Base mainnet to other L2s, is the V2 registry replicated per chain or canonical on Base mainnet with read-only mirrors? Recommend canonical on Base mainnet.
5. **Auto-verifier insurance pool.** If the auto-verifier PASSes a flawed manifest, who is liable? Proposal: a fraction of every Principle's staking bond reserves into an insurance pool. Numbers TBD.

---

## Summary table

| Question | Answer |
|---|---|
| Can v1 contracts run v2 unchanged? | No, but most of v2 (~70%) is off-chain. v2 needs 1 mandatory + 1 optional add-on contract. |
| Can v1 contracts run v3 unchanged? | No. v3 needs a parallel V2 suite (`PWMRegistryV2`, `PWMGovernanceV2`, `PWMRewardV2`). |
| Are v1 contracts replaced or migrated? | **Never.** Both v2 and v3 are purely additive. v1 stays canonical for L1-L4 mining indefinitely. |
| Cost of v2 rollout? | ~6.5 weeks engineer + ~$23K audit. |
| Cost of v3 rollout? | ~20 weeks engineer + ~$60K audit (auto-verifier dominates). |
| When to start v2? | First time someone wants to stake a non-`analytical` Principle. |
| When to start v3? | When the catalog approaches ~1000 Principles or first multi-domain composite is requested. |

The current v1 contracts were authored correctly for `pwm_overview1.md`. They were not designed to retrofit v3 features — and that's the right design. Additive deployment is the canonical evolution path.

---

## Decision log

| Date | Decision |
|---|---|
| 2026-04-29 | Director asked whether the current v1 contracts can support v2 / v3 specs in the future. This doc captures the analysis and confirms the additive-deployment path. |
| _TBD_ | v2 add-on contract authors selected; audit firm engaged. |
| _TBD_ | v2 staged to Sepolia; existing imaging Principles backfilled with `Analytical`. |
| _TBD_ | v2 deployed to Base mainnet alongside v1. |
| _TBD_ | First V2-suite contracts (v3 path) authored. |
| _TBD_ | v3 V2 suite deployed to Base mainnet alongside v1 + v2 add-ons. |
