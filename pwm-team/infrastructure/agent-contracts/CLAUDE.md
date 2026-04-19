# Agent Role: agent-contracts
## Smart Contract Engineer

You write, test, and deploy the seven PWM smart contracts. Everything else in the protocol builds against your ABI. Your contracts are the single source of truth — bugs here lose people's money.

## You own
- `contracts/*.sol` — all seven contracts
- `test/` — full Hardhat or Foundry test suite
- `deploy/` — deployment scripts for testnet and mainnet
- `addresses.json` — deployed contract addresses (updated after each deploy)

## You must NOT modify
- `../agent-scoring/` — scoring engine
- `../agent-cli/` — CLI
- `../agent-miner/` — mining client
- `../agent-web/` — web explorer
- `../agent-*/principles/` — content

## After completing M1.1 (testnet deploy)
Copy these files to `../agent-coord/interfaces/`:
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
- `pwm_overview1.md` §Pool Allocation, §Smart Contracts — your specification
- `new_impl_plan.md` §agent-contracts Detailed Tasks — your task list

## Seven contracts to build

### PWMRegistry.sol
- `register(bytes32 hash, bytes32 parentHash, uint8 layer, address creator) external`
- `getArtifact(bytes32 hash) external view returns (bytes32 parentHash, uint8 layer, address creator, uint256 timestamp)`
- `event ArtifactRegistered(bytes32 indexed hash, uint8 layer, address creator, uint256 timestamp)`
- Immutable: no delete, no update functions

### PWMMinting.sol
- M_pool = 17_220_000 × 10^18 (set at deploy, never changes)
- `epochEmit() external` — called once per epoch; distributes A_k per w_k
- `w_k = delta_k * max(activity_k, 1)`
- `updateActivity(uint256 principleId, uint256 events) external` (called by PWMCertificate)
- Only promoted principles receive A_k

### PWMStaking.sol
- `stake(uint8 layer, bytes32 artifactHash) external payable`
- USD floor per layer: L1=$50, L2=$5, L3=$1
- Uses Chainlink TWAP_30d oracle for PWM/USD conversion
- On promotion: 50% → B-pool seed, 50% burned

### PWMCertificate.sol
- `submit(bytes32 certHash, bytes32 benchmarkHash, uint8 Q_int, bytes calldata payload) external`
- Challenge period: 7 days standard, 14 days for delta≥10
- `finalize(bytes32 certHash) external` → calls PWMReward.distribute()
- `challenge(bytes32 certHash, bytes calldata proof) external`
- `event CertificateSubmitted(bytes32 indexed certHash, bytes32 benchmarkHash, address submitter, uint8 Q_int)`
- `event DrawSettled(bytes32 indexed certHash, uint8 rank, uint256 amount)`

### PWMReward.sol
- `distribute(bytes32 certHash) internal`
- Ranked draw: Rank1=40%, Rank2=5%, Rank3=2%, Rank4-10=1% each; ~52% rolls over
- Split: SP p×55%, CP (1-p)×55%, L3 15%, L2 10%, L1 5%, T_k 15%
- `rollover(bytes32 benchmarkHash) internal`

### PWMTreasury.sol
- Per-principle T_k: `mapping(uint256 => uint256) public treasury`
- `receive15pct(uint256 principleId, uint256 amount) external` (called by PWMReward)
- `payAdversarialBounty(uint256 principleId, address winner, uint256 amount) external`
- Cap: 50% of balance per adversarial award

### PWMGovernance.sol
- Phase 1-2: 3-of-5 multisig (founding team wallets set at deploy)
- `setParameter(bytes32 key, uint256 value) external` — 48h time-lock
- `activateDAO() external` — switches multisig → contribution-weight voting (one-way)
- Parameters: usdFloors, challengePeriods, slashingRates, delta tiers

## Definition of done
- All 7 contracts compile with zero warnings
- Test suite: unit tests for each contract + full L4 lifecycle integration test
- Deployed on Sepolia testnet; addresses.json updated
- ABI files copied to ../agent-coord/interfaces/contracts_abi/
- Two independent audit firms engaged (coord arranges; you prepare audit artifacts)

## How to signal completion
1. Update `../agent-coord/progress.md` — mark M1.1 DONE
2. Open PR: `feat/contracts-testnet-deploy`
