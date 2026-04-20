# agent-contracts: Validation Checklist

Run every check below before merging the contracts PR. All values reference `pwm_overview1.md` (canonical spec).

---

## V1 — Files Exist

- [ ] `contracts/PWMRegistry.sol`
- [ ] `contracts/PWMMinting.sol`
- [ ] `contracts/PWMStaking.sol`
- [ ] `contracts/PWMCertificate.sol`
- [ ] `contracts/PWMReward.sol`
- [ ] `contracts/PWMTreasury.sol`
- [ ] `contracts/PWMGovernance.sol`
- [ ] `test/PWMRegistry.test.js`
- [ ] `test/PWMMinting.test.js`
- [ ] `test/PWMStaking.test.js`
- [ ] `test/PWMCertificate.test.js`
- [ ] `test/PWMReward.test.js`
- [ ] `test/PWMTreasury.test.js`
- [ ] `test/PWMGovernance.test.js`
- [ ] `test/integration_l4_lifecycle.test.js`
- [ ] `deploy/testnet.js`
- [ ] `addresses.json`
- [ ] `hardhat.config.js`

**Verify:**
```bash
npx hardhat compile  # zero warnings
npx hardhat test     # all pass
```

---

## V2 — PWMRegistry.sol

- [ ] `register(bytes32 hash, bytes32 parentHash, uint8 layer, address creator) external`
- [ ] `getArtifact(bytes32 hash) external view returns (bytes32, uint8, address, uint256)`
- [ ] `event ArtifactRegistered(bytes32 indexed hash, uint8 layer, address creator, uint256 timestamp)`
- [ ] Immutable: **no** delete or update functions exist
- [ ] Revert if hash already registered
- [ ] Layers 1, 2, 3, 4 all accepted

**Test:**
```bash
npx hardhat test test/PWMRegistry.test.js
```
- [ ] Register artifact → getArtifact returns correct fields
- [ ] Re-register same hash → reverts with error
- [ ] Layer values 1/2/3/4 all accepted

---

## V3 — PWMMinting.sol

- [ ] `M_POOL = 17_220_000 * 10**18` (82% of 21M)
- [ ] `epochEmit() external` — Zeno emission: `A_k = (M_pool - M_emitted) * w_k / sum(w_j)`
- [ ] `w_k = delta_k * max(activity_k, 1)` per principle
- [ ] `updateActivity(uint256 principleId, uint256 events) external` — only PWMCertificate can call
- [ ] `promotionRegistry: mapping(uint256 => bool)` — only promoted principles receive A_k
- [ ] `setPromotion(uint256 principleId, bool status) external` — only governance can call

**Canonical formula check:**
```
A_k = (M_pool - M(t)) × w_k / Σ(w_j for all promoted j)
```

**Test:**
```bash
npx hardhat test test/PWMMinting.test.js
```
- [ ] epochEmit distributes correct amounts proportional to w_k
- [ ] Non-promoted principle gets 0
- [ ] M_emitted increases after each epoch
- [ ] Only PWMCertificate can call updateActivity (others revert)
- [ ] Only governance can call setPromotion (others revert)

---

## V4 — PWMStaking.sol

### Staking tiers (canonical values — MUST match exactly):

| Layer | USD Target | PWM Floor | Formula |
|-------|-----------|-----------|---------|
| L1 Principle | $50 | 10 PWM | `S = max(10, ceil(50 / TWAP_30d))` |
| L2 Spec | $5 | 2 PWM | `S = max(2, ceil(5 / TWAP_30d))` |
| L3 I-benchmark | $1 | 1 PWM | `S = max(1, ceil(1 / TWAP_30d))` |

- [ ] `stake(uint8 layer, bytes32 artifactHash) external payable`
- [ ] Uses Chainlink `AggregatorV3Interface` for TWAP_30d
- [ ] USD floors enforced (cannot stake less than floor regardless of TWAP)
- [ ] PWM floors enforced (minimum 10/2/1 PWM regardless of USD)

### Stake outcomes:

| Outcome | Fate |
|---------|------|
| Promotion (graduation) | 50% returned to contributor, 50% locked as B-pool seed |
| Challenge upheld | 50% burned, 50% to challenger |
| Fraud | 100% burned, artifact permanently delisted |

- [ ] On promotion: calls `PWMReward.seedBPool()` with 50%
- [ ] On challenge upheld: 50% sent to `address(0)`, 50% to challenger address
- [ ] On fraud: 100% sent to `address(0)`

**Test:**
```bash
npx hardhat test test/PWMStaking.test.js
```
- [ ] Staking with mock Chainlink oracle at various TWAP values
- [ ] USD floor enforced when TWAP is high
- [ ] PWM floor enforced when TWAP is low
- [ ] Graduation splits correctly (50/50)
- [ ] Challenge slashing splits correctly (50/50)
- [ ] Fraud burns 100%

---

## V5 — PWMCertificate.sol

- [ ] `submit(bytes32 certHash, bytes32 benchmarkHash, uint8 Q_int, address acWallet, address cpWallet, uint16 shareRatioP) external`
- [ ] `shareRatioP` = p × 10000, enforced: p ∈ [0.10, 0.90] → shareRatioP ∈ [1000, 9000]
- [ ] Challenge period: 7 days standard
- [ ] Challenge period: 14 days if benchmark's principle has δ ≥ 10
- [ ] `finalize(bytes32 certHash) external` — only callable after challenge period expires
- [ ] finalize calls `PWMReward.distribute()`
- [ ] `challenge(bytes32 certHash, bytes calldata proof) external` — slashing if proof valid
- [ ] `event CertificateSubmitted(bytes32 indexed certHash, bytes32 benchmarkHash, address submitter, uint8 Q_int)`
- [ ] `event DrawSettled(bytes32 indexed certHash, uint8 rank, uint256 amount, address ac, address cp)`

**Test:**
```bash
npx hardhat test test/PWMCertificate.test.js
```
- [ ] Submit → finalize after 7 days → reward distributed
- [ ] Submit → finalize before 7 days → reverts
- [ ] Submit with δ ≥ 10 → finalize after 14 days → works
- [ ] Submit with δ ≥ 10 → finalize at 13 days → reverts
- [ ] Challenge within period → slashing triggers
- [ ] Challenge after period expires → reverts
- [ ] shareRatioP < 1000 → reverts
- [ ] shareRatioP > 9000 → reverts

---

## V6 — PWMReward.sol

### Ranked draw percentages (MUST match exactly):

| Rank | Draw % |
|------|--------|
| 1 | 40% |
| 2 | 5% |
| 3 | 2% |
| 4 | 1% |
| 5 | 1% |
| 6 | 1% |
| 7 | 1% |
| 8 | 1% |
| 9 | 1% |
| 10 | 1% |
| Rollover | ~52% |

### Per-draw split (MUST match exactly):

| Recipient | Share |
|-----------|-------|
| AC (Algorithm Creator) | p × 55% |
| CP (Compute Provider) | (1-p) × 55% |
| L3 benchmark creator | 15% |
| L2 spec author | 10% |
| L1 principle creator | 5% |
| T_k protocol treasury | 15% |
| **Total** | **100%** |

- [ ] `distribute(bytes32 certHash) internal` — only PWMCertificate can call
- [ ] `rollover(bytes32 benchmarkHash) internal` — undistributed stays in pool
- [ ] `seedBPool(uint256 principleId) external payable` — receives promotion stake 50%
- [ ] Rank 10 is the last paid rank; Rank 11+ receives nothing

**Numerical verification (worked example from spec):**
With pool = 1000 PWM, p = 0.30:
- [ ] Rank 1 draw = 400.00 PWM
- [ ] Rank 1 AC share = 400 × 0.30 × 0.55 = 66.00 PWM
- [ ] Rank 1 CP share = 400 × 0.70 × 0.55 = 154.00 PWM
- [ ] Rank 1 L3 share = 400 × 0.15 = 60.00 PWM
- [ ] Rank 1 L2 share = 400 × 0.10 = 40.00 PWM
- [ ] Rank 1 L1 share = 400 × 0.05 = 20.00 PWM
- [ ] Rank 1 T_k share = 400 × 0.15 = 60.00 PWM
- [ ] Rollover ≈ 520.65 PWM

**Test:**
```bash
npx hardhat test test/PWMReward.test.js
```
- [ ] Rank draw math correct for ranks 1-10
- [ ] Rollover accumulates correctly
- [ ] Split percentages verified per recipient
- [ ] seedBPool receives ETH/PWM correctly

---

## V7 — PWMTreasury.sol

- [ ] `mapping(uint256 => uint256) public treasury` — T_k per principle
- [ ] `receive15pct(uint256 principleId, uint256 amount) external` — only PWMReward can call
- [ ] `payAdversarialBounty(uint256 principleId, address winner, uint256 amount) external` — only governance
- [ ] Cap: `amount <= treasury[principleId] / 2` (50% cap)
- [ ] No global treasury — each principle is self-funded

**Test:**
```bash
npx hardhat test test/PWMTreasury.test.js
```
- [ ] T_k accumulates from receive15pct calls
- [ ] Adversarial bounty respects 50% cap
- [ ] Bounty payment above 50% → reverts
- [ ] Only PWMReward can call receive15pct (others revert)
- [ ] Only governance can call payAdversarialBounty (others revert)

---

## V8 — PWMGovernance.sol

- [ ] 3-of-5 multisig: `address[5] public founders` set at deploy
- [ ] `setParameter(bytes32 key, uint256 value) external` — 48h time-lock
- [ ] `activateDAO() external` — one-way switch; requires 3-of-5; disables multisig permanently
- [ ] Parameters: `USD_FLOORS`, `CHALLENGE_PERIODS`, `SLASHING_RATES`, `DELTA_TIERS`
- [ ] Contribution-weighted voting after DAO activation:
  `voting_weight = w1*(Reserve grants) + w2*(upstream royalties) + w3*(best Q_p) + w4*sqrt(PWM held)`

**Test:**
```bash
npx hardhat test test/PWMGovernance.test.js
```
- [ ] Parameter change requires 3-of-5 approval
- [ ] Parameter change has 48h time-lock (cannot execute before)
- [ ] DAO activation is irreversible (cannot re-enable multisig)
- [ ] After DAO activation, multisig functions revert

---

## V9 — Integration Test (Full L4 Lifecycle)

```bash
npx hardhat test test/integration_l4_lifecycle.test.js
```

This single test must cover the complete flow:

1. [ ] Register L1, L2, L3 artifacts in PWMRegistry
2. [ ] Stake L2 and L3 in PWMStaking (correct amounts per tier)
3. [ ] Submit L4 certificate in PWMCertificate (with valid Q_int, shareRatioP)
4. [ ] Advance time past challenge period (`hardhat_mine`)
5. [ ] Finalize certificate → `PWMReward.distribute()` fires
6. [ ] Verify AC address received `p × 55%` of draw
7. [ ] Verify CP address received `(1-p) × 55%` of draw
8. [ ] Verify L3 creator received 15% of draw
9. [ ] Verify L2 author received 10% of draw
10. [ ] Verify L1 creator received 5% of draw
11. [ ] Verify T_k balance increased by 15% of draw in PWMTreasury
12. [ ] Verify rollover ≈ 52% stays in benchmark pool

---

## V10 — Testnet Deployment

- [ ] All 7 contracts deployed on Sepolia
- [ ] `addresses.json` contains all 7 contract addresses under `testnet` key
- [ ] Deploy order matches dependency chain: `PWMGovernance → PWMRegistry → PWMTreasury → PWMReward → PWMStaking → PWMCertificate → PWMMinting`
- [ ] All contracts verified on Sepolia Etherscan (source code readable)
- [ ] ABI files copied to `../../coordination/agent-coord/interfaces/contracts_abi/` (7 files)
- [ ] `addresses.json` copied to `../../coordination/agent-coord/interfaces/`
- [ ] `cert_schema.json` copied to `../../coordination/agent-coord/interfaces/`
- [ ] Genesis 500 principle hashes batch-registered on testnet
- [ ] Test PWM faucet deployed with `drip()` function

**Verify:**
```bash
# Check addresses.json structure
python3 -c "
import json
a = json.load(open('addresses.json'))
required = ['PWMRegistry','PWMMinting','PWMStaking','PWMCertificate','PWMReward','PWMTreasury','PWMGovernance']
for r in required:
    assert r in a['testnet'], f'Missing {r}'
    assert a['testnet'][r].startswith('0x'), f'Invalid address for {r}'
print('All 7 contracts present with valid addresses')
"
```

---

## V11 — Access Control Matrix

Verify each contract function's caller restriction:

| Function | Allowed Caller | Others Revert? |
|----------|---------------|----------------|
| PWMMinting.updateActivity() | PWMCertificate only | [ ] |
| PWMMinting.setPromotion() | PWMGovernance only | [ ] |
| PWMReward.distribute() | PWMCertificate only | [ ] |
| PWMReward.seedBPool() | PWMStaking only | [ ] |
| PWMTreasury.receive15pct() | PWMReward only | [ ] |
| PWMTreasury.payAdversarialBounty() | PWMGovernance only | [ ] |
| PWMGovernance.setParameter() | 3-of-5 multisig | [ ] |
| PWMGovernance.activateDAO() | 3-of-5 multisig | [ ] |

---

## V12 — Zero Warnings

```bash
npx hardhat compile 2>&1 | grep -i warning
# Must return empty
```

- [ ] All contracts compile with zero Solidity warnings
- [ ] No unused variables, no shadowing, no deprecated features
