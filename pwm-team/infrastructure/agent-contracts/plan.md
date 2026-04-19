# agent-contracts: Execution Plan

Read `CLAUDE.md` first (your role and all contract specs). This file is your step-by-step work order.

---

## Before You Start

- [ ] Read `CLAUDE.md` — full specs for all 7 contracts are there.
- [ ] Read `../../papers/Proof-of-Solution/pwm_overview1.md` §Pool Allocation, §Smart Contracts, §Bootstrap Phase.
- [ ] Read `../../new_impl_plan.md` §agent-contracts Detailed Tasks.
- [ ] Initialize Hardhat project:
  ```bash
  cd infrastructure/agent-contracts
  npm init -y
  npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
  npx hardhat init  # choose "Create a JavaScript project"
  ```

---

## Step 1 — Write PWMRegistry.sol

- [ ] **1.1** Create `contracts/PWMRegistry.sol`.
- [ ] **1.2** Implement:
  - `register(bytes32 hash, bytes32 parentHash, uint8 layer, address creator) external`
  - `getArtifact(bytes32 hash) external view returns (bytes32, uint8, address, uint256)`
  - `event ArtifactRegistered(bytes32 indexed hash, uint8 layer, address creator, uint256 timestamp)`
  - Storage: `mapping(bytes32 => Artifact) private _artifacts`
  - Guard: revert if hash already registered (immutable)
- [ ] **1.3** Write `test/PWMRegistry.test.js`:
  - Register artifact → getArtifact returns correct fields
  - Re-register same hash → reverts
  - Layer 1/2/3/4 all accepted
- [ ] **1.4** `npx hardhat test test/PWMRegistry.test.js` → all pass.

---

## Step 2 — Write PWMMinting.sol

- [ ] **2.1** Create `contracts/PWMMinting.sol`.
- [ ] **2.2** Implement:
  - `uint256 public constant M_POOL = 17_220_000 * 10**18`
  - `epochEmit() external` — Zeno emission: `A_k = (M_pool - M_emitted) * w_k / sum(w_j)`
  - `updateActivity(uint256 principleId, uint256 benchmarkId, uint256 events) external` (only PWMCertificate can call)
  - `promotionRegistry: mapping(uint256 => bool)` — only promoted principles receive A_k
  - `setPromotion(uint256 principleId, bool status) external` (only governance)
- [ ] **2.3** Write tests: epochEmit distributes correct amounts; non-promoted principle gets 0.
- [ ] **2.4** `npx hardhat test test/PWMMinting.test.js` → all pass.

---

## Step 3 — Write PWMStaking.sol

- [ ] **3.1** Create `contracts/PWMStaking.sol`.
- [ ] **3.2** Implement:
  - USD-denominated staking with formula `S = max(PWM_floor, ceil(USD_target / TWAP_30d))`:
    - L2 spec: floor = 500 PWM, target = $50
    - L3 benchmark: floor = 200 PWM, target = $20
    - L4 solution: floor = 50 PWM, target = $5
    (stored in contract, adjustable via governance)
  - Chainlink TWAP_30d oracle: `AggregatorV3Interface` for PWM/USD price
  - `stake(uint8 layer, bytes32 artifactHash) external payable`
  - On promotion: 50% → B-pool seed (`PWMReward.seedBPool()`), 50% burned (`address(0).transfer`)
- [ ] **3.3** Write tests with mock Chainlink oracle. Confirm USD floor enforced.
- [ ] **3.4** `npx hardhat test test/PWMStaking.test.js` → all pass.

---

## Step 4 — Write PWMCertificate.sol

- [ ] **4.1** Create `contracts/PWMCertificate.sol`.
- [ ] **4.2** Implement:
  - `submit(bytes32 certHash, bytes32 benchmarkHash, uint8 Q_int, address acWallet, address cpWallet, uint16 shareRatioP) external`
    - `shareRatioP = p × 10000`, where `p ∈ [0.10, 0.90]`
  - Challenge period: 7 days (standard), 14 days if benchmark delta ≥ 10
  - `finalize(bytes32 certHash) external` → callable after challenge period; calls `PWMReward.distribute()`
  - `challenge(bytes32 certHash, bytes calldata proof) external` → slashing if proof valid
  - `event CertificateSubmitted(bytes32 indexed certHash, bytes32 benchmarkHash, address submitter, uint8 Q_int)`
  - `event DrawSettled(bytes32 indexed certHash, uint8 rank, uint256 amount, address ac, address cp)`
- [ ] **4.3** Write tests: submit → finalize after 7 days → reward distributed. Challenge within period → slashing.
- [ ] **4.4** `npx hardhat test test/PWMCertificate.test.js` → all pass.

---

## Step 5 — Write PWMReward.sol

- [ ] **5.1** Create `contracts/PWMReward.sol`.
- [ ] **5.2** Implement ranked draw:
  - Rank 1 = 40%, Rank 2 = 5%, Rank 3 = 2%, Rank 4–10 = 1% each → ~52% rollover
  - Split per draw: AC p×55%, CP (1-p)×55%, L3 15%, L2 10%, L1 5%, T_k 15%
  - `distribute(bytes32 certHash) external` (only PWMCertificate can call)
  - `rollover(bytes32 benchmarkHash) internal`
  - `seedBPool(uint256 principleId) external payable` (receives promotion stake)
- [ ] **5.3** Write tests: rank draw math correct; rollover accumulates.
- [ ] **5.4** `npx hardhat test test/PWMReward.test.js` → all pass.

---

## Step 6 — Write PWMTreasury.sol

- [ ] **6.1** Create `contracts/PWMTreasury.sol`.
- [ ] **6.2** Implement:
  - `mapping(uint256 => uint256) public treasury` — T_k per principle
  - `receive15pct(uint256 principleId, uint256 amount) external` (only PWMReward)
  - `payAdversarialBounty(uint256 principleId, address winner, uint256 amount) external` (only governance)
  - Cap: amount ≤ 50% of treasury[principleId]
- [ ] **6.3** Write tests: T_k accumulates; bounty payment respects 50% cap.
- [ ] **6.4** `npx hardhat test test/PWMTreasury.test.js` → all pass.

---

## Step 7 — Write PWMGovernance.sol

- [ ] **7.1** Create `contracts/PWMGovernance.sol`.
- [ ] **7.2** Implement:
  - 3-of-5 multisig: `address[5] public founders` (set at deploy)
  - `setParameter(bytes32 key, uint256 value) external` — 48h time-lock
  - `activateDAO() external` — one-way switch; requires 3-of-5 approval; disables multisig
  - Parameters: `USD_FLOORS`, `CHALLENGE_PERIODS`, `SLASHING_RATES`, `DELTA_TIERS`
- [ ] **7.3** Write tests: parameter change time-lock enforced; DAO activation irreversible.
- [ ] **7.4** `npx hardhat test test/PWMGovernance.test.js` → all pass.

---

## Step 8 — Integration Test (Full L4 Lifecycle)

- [ ] **8.1** Write `test/integration_l4_lifecycle.test.js`:
  ```
  1. Register L1, L2, L3 artifacts in PWMRegistry
  2. Stake L2 and L3 in PWMStaking
  3. Submit L4 certificate in PWMCertificate
  4. Advance time past challenge period (hardhat_mine)
  5. Finalize certificate → PWMReward.distribute() fires
  6. Confirm AC, CP, L3, L2, L1 addresses received correct amounts
  7. Confirm T_k balance increased in PWMTreasury
  8. Confirm rollover ~52% stays in benchmark pool
  ```
- [ ] **8.2** `npx hardhat test test/integration_l4_lifecycle.test.js` → all pass.

---

## Step 9 — Testnet Deploy

- [ ] **9.1** Set up Sepolia RPC in `hardhat.config.js`:
  ```js
  networks: {
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL,
      accounts: [process.env.DEPLOYER_PRIVATE_KEY]
    }
  }
  ```
- [ ] **9.2** Write `deploy/testnet.js` — deploy all 7 contracts in dependency order:
  `PWMGovernance → PWMRegistry → PWMTreasury → PWMReward → PWMStaking → PWMCertificate → PWMMinting`
- [ ] **9.3** Run deploy: `npx hardhat run deploy/testnet.js --network sepolia`
- [ ] **9.4** Update `addresses.json`:
  ```json
  {
    "testnet": {
      "network": "sepolia",
      "PWMRegistry": "0x...",
      "PWMMinting": "0x...",
      "PWMStaking": "0x...",
      "PWMCertificate": "0x...",
      "PWMReward": "0x...",
      "PWMTreasury": "0x...",
      "PWMGovernance": "0x..."
    }
  }
  ```
- [ ] **9.5** Verify contracts on Sepolia Etherscan (or equivalent block explorer).
- [ ] **9.6** Deploy faucet: simple ERC20 test PWM token + `drip()` function.

---

## Step 10 — Publish Interfaces

- [ ] **10.1** Extract ABI files: `npx hardhat compile` → artifacts appear in `artifacts/contracts/`
- [ ] **10.2** Copy ABI JSON files to `../../coordination/agent-coord/interfaces/contracts_abi/`
- [ ] **10.3** Copy `addresses.json` to `../../coordination/agent-coord/interfaces/`
- [ ] **10.4** Copy `cert_schema.json` to `../../coordination/agent-coord/interfaces/`

---

## Step 11 — Signal Completion

- [ ] **11.1** Update `../../coordination/agent-coord/progress.md` — mark M1.1 `DONE`.
- [ ] **11.2** Open PR: `feat/contracts-testnet-deploy`
  - Include: all 7 contracts, full test suite, addresses.json, ABI files
  - PR description: list each contract + its test count
