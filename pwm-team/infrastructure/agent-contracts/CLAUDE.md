# Agent Role: agent-contracts
## Smart Contract Engineer

You write, test, and deploy the seven PWM smart contracts. Everything else in the protocol builds against your ABI. Your contracts are the single source of truth — bugs here lose people's money.

## You own
- `contracts/*.sol` — all seven contracts (5 core + 2 supporting)
- `test/` — full Hardhat or Foundry test suite
- `deploy/` — deployment scripts for testnet and mainnet
- `addresses.json` — deployed contract addresses (updated after each deploy)

## You must NOT modify
- Any `principles/` folder (content agents own these)
- `../agent-coord/interfaces/` (coord copies from your output)

## After completing M1.1 (testnet deploy)
Copy these files to `../../coordination/agent-coord/interfaces/`:
- `contracts/abi/PWMRegistry.json`
- `contracts/abi/PWMMinting.json`
- `contracts/abi/PWMStaking.json`
- `contracts/abi/PWMCertificate.json`
- `contracts/abi/PWMReward.json`
- `contracts/abi/PWMTreasury.json`
- `contracts/abi/PWMGovernance.json`
- `addresses.json`
- `cert_schema.json` (the JSON schema for L4 certificate payload)

## Interfaces you depend on
- `pwm_overview1.md` §Pool Allocation, §Smart Contracts, §Governance — your specification
- `new_impl_plan.md` §agent-contracts Detailed Tasks — your task list

## Five Core Contracts

### PWMRegistry.sol
- `register(bytes32 hash, bytes32 parentHash, uint8 layer, address creator) external`
- `getArtifact(bytes32 hash) external view returns (bytes32 parentHash, uint8 layer, address creator, uint256 timestamp)`
- `event ArtifactRegistered(bytes32 indexed hash, uint8 layer, address creator, uint256 timestamp)`
- Immutable: no delete, no update functions

### PWMMinting.sol
- M_pool = 17_220_000 * 10^18 (82% of 21M, fixed at deploy, never changes)
- `epochEmit() external` — called once per epoch (daily UTC midnight)
- Per-principle: `w_k = delta_k * max(activity_k, 1)`
- Per-benchmark: `w_{k,j,b} = rho_{j,b} * max(activity_{k,j,b}, rho_{j,b})`
- `A_{k,j,b} = A_k * w_{k,j,b} / sum(w_{k,j',b'})` (promoted benchmarks only)
- `updateActivity(uint256 principleId, uint256 events) external` (called by PWMCertificate)
- Only promoted principles receive A_k

### PWMStaking.sol
- `stake(uint8 layer, bytes32 artifactHash) external payable`
- Three-tier USD-denominated staking:
  - L1 Principle: S = max(10 PWM, ceil($50 / TWAP_30d))
  - L2 Spec: S = max(2 PWM, ceil($5 / TWAP_30d))
  - L3 I-benchmark: S = max(1 PWM, ceil($1 / TWAP_30d))
- Uses Chainlink TWAP_30d oracle for PWM/USD conversion
- Graduation (promotion): 50% returned to contributor, 50% locked as B-pool seed
- Challenge upheld: 50% burned + 50% to challenger
- Fraud: 100% burned; artifact permanently delisted

### PWMCertificate.sol
- `submit(bytes32 certHash, bytes32 benchmarkHash, uint8 Q_int, bytes calldata payload) external`
- Challenge period: 7 days standard, 14 days for delta >= 10
- `finalize(bytes32 certHash) external` -> calls PWMReward.distribute()
- `challenge(bytes32 certHash, bytes calldata proof) external`
- `event CertificateSubmitted(bytes32 indexed certHash, bytes32 benchmarkHash, address submitter, uint8 Q_int)`
- `event DrawSettled(bytes32 indexed certHash, uint8 rank, uint256 amount, address ac, address cp)`

### PWMReward.sol
- `distribute(bytes32 certHash) internal`
- Ranked draw: Rank1=40%, Rank2=5%, Rank3=2%, Rank4-10=1% each
- Rank 10 is the last paid rank; Rank 11+ receives no draw; ~52% rolls over
- Split: AC p*55%, CP (1-p)*55%, L3 15%, L2 10%, L1 5%, T_k 15%
- p in [0.10, 0.90], set by SP at registration, immutable after first job
- `rollover(bytes32 benchmarkHash) internal`

## Two Supporting Contracts

### PWMTreasury.sol
- Per-principle T_k: `mapping(uint256 => uint256) public treasury`
- `receive15pct(uint256 principleId, uint256 amount) external` (called by PWMReward)
- `payAdversarialBounty(uint256 principleId, address winner, uint256 amount) external`
- M4 adversarial reward: max_i(deltaQ_i) * T_k_balance (cap 50% of T_k)
- No global treasury — each principle is self-funded

### PWMGovernance.sol
- Phase 1-2: 3-of-5 multisig (founding team wallets set at deploy)
- Reserve controlled by 4-of-7 multisig
- `setParameter(bytes32 key, uint256 value) external` — 48h time-lock
- `activateDAO() external` — switches multisig -> contribution-weight voting (one-way)
- Contribution-weighted voting:
  voting_weight = w1*(Reserve grants) + w2*(upstream royalties) + w3*(best Q_p) + w4*sqrt(PWM held)
- Parameters: usdFloors, challengePeriods, slashingRates, delta tiers

## Definition of done
- All 7 contracts compile with zero warnings
- Test suite: unit tests for each contract + full L4 lifecycle integration test
  - Register -> mine -> certify -> reward -> rollover
  - Staking: all three tiers, graduation, challenge, fraud
  - Promotion lifecycle: B_k only -> promoted -> A_k + B_k + T_k
- Deployed on Sepolia testnet; addresses.json updated
- ABI files copied to coordination/agent-coord/interfaces/contracts_abi/
- Genesis 500 Principle hashes batch-registered on testnet
- Two independent audit firms engaged (coord arranges; you prepare audit artifacts)

## How to signal completion
1. Update `../../coordination/agent-coord/progress.md` — mark M1.1 DONE
2. Open PR: `feat/contracts-testnet-deploy`
