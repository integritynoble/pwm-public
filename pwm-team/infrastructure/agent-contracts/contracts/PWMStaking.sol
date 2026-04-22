// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPWMReward {
    function seedBPool(bytes32 benchmarkHash) external payable;
}

/// @title PWMStaking
/// @notice Fixed-PWM staking per tier. No USD oracle — each tier has a governance-tunable
///         PWM amount (initial defaults taken from pwm_overview1.md floor values).
///
///   L1 Principle:    10 PWM
///   L2 Spec:          2 PWM
///   L3 I-benchmark:   1 PWM
///
/// Stake fates
///   Graduation (promotion succeeds): 50% returned to staker, 50% → PWMReward.seedBPool
///   Challenge upheld:                50% burned, 50% → challenger
///   Fraud:                          100% burned; artifact delisted
contract PWMStaking {
    uint8  public constant LAYER_PRINCIPLE = 1;
    uint8  public constant LAYER_SPEC      = 2;
    uint8  public constant LAYER_BENCHMARK = 3;

    address public constant BURN_SINK = 0x000000000000000000000000000000000000dEaD;

    address public governance;
    IPWMReward public reward;

    mapping(uint8 => uint256) public stakeAmount; // layer => required PWM amount (wei)

    /// @notice Running total of all Active stake value across all artifacts, in wei.
    ///         Incremented on stake(), decremented on resolution (graduate /
    ///         slashForChallenge / slashForFraud) when the funds leave the
    ///         contract. Used to enforce maxTotalStakeWei.
    uint256 public totalActiveStakeWei;

    /// @notice Soft cap on totalActiveStakeWei. Zero (default) means unlimited.
    ///         Governance-settable. Enforced on stake() — lowering the cap
    ///         below the current total just blocks further stakes, it does
    ///         NOT forcibly refund existing stakers.
    ///
    ///         Rationale: bounds blast radius during the pre-audit mainnet
    ///         soft-launch (see AUDIT_FREE_PATH.md Track D). Lifted to a
    ///         higher value or to 0 (unlimited) once audited.
    uint256 public maxTotalStakeWei;

    enum Status { None, Active, Graduated, Slashed, Fraud }
    struct Stake {
        address staker;
        uint8   layer;
        uint256 amount;
        Status  status;
    }
    mapping(bytes32 => Stake) public stakes; // artifactHash => stake

    event StakeAmountUpdated(uint8 indexed layer, uint256 amount);
    event Staked(bytes32 indexed artifactHash, uint8 indexed layer, address indexed staker, uint256 amount);
    event Graduated(bytes32 indexed artifactHash, address indexed staker, uint256 returned, uint256 seeded);
    event ChallengeUpheld(bytes32 indexed artifactHash, address indexed challenger, uint256 burned, uint256 toChallenger);
    event FraudSlashed(bytes32 indexed artifactHash, uint256 burned);
    event GovernanceUpdated(address indexed newGovernance);
    event RewardUpdated(address indexed newReward);
    event MaxTotalStakeWeiUpdated(uint256 newMax);

    modifier onlyGovernance() { require(msg.sender == governance, "PWMStaking: not governance"); _; }

    constructor(address initialGovernance) {
        require(initialGovernance != address(0), "PWMStaking: zero governance");
        governance = initialGovernance;
        // defaults from pwm_overview1.md §Three-Tier Staking (floor values)
        stakeAmount[LAYER_PRINCIPLE] = 10 ether; // 10 PWM
        stakeAmount[LAYER_SPEC]      = 2 ether;  // 2 PWM
        stakeAmount[LAYER_BENCHMARK] = 1 ether;  // 1 PWM
    }

    // ---------- governance ----------

    function setGovernance(address x) external onlyGovernance {
        require(x != address(0), "PWMStaking: zero governance");
        governance = x;
        emit GovernanceUpdated(x);
    }
    function setReward(address x) external onlyGovernance {
        require(x != address(0), "PWMStaking: zero reward");
        reward = IPWMReward(x);
        emit RewardUpdated(x);
    }
    function setStakeAmount(uint8 layer, uint256 amount) external onlyGovernance {
        require(layer >= LAYER_PRINCIPLE && layer <= LAYER_BENCHMARK, "PWMStaking: bad layer");
        require(amount > 0, "PWMStaking: zero amount");
        stakeAmount[layer] = amount;
        emit StakeAmountUpdated(layer, amount);
    }

    /// @notice Set the total-stake cap. Pass 0 to disable (unlimited).
    function setMaxTotalStakeWei(uint256 newMax) external onlyGovernance {
        maxTotalStakeWei = newMax;
        emit MaxTotalStakeWeiUpdated(newMax);
    }

    // ---------- staking ----------

    /// @notice Stake the exact per-layer amount against an artifact. Callable once per artifact.
    function stake(uint8 layer, bytes32 artifactHash) external payable {
        require(layer >= LAYER_PRINCIPLE && layer <= LAYER_BENCHMARK, "PWMStaking: bad layer");
        require(artifactHash != bytes32(0), "PWMStaking: zero hash");
        require(stakes[artifactHash].status == Status.None, "PWMStaking: already staked");
        uint256 required = stakeAmount[layer];
        require(msg.value == required, "PWMStaking: wrong amount");

        uint256 newTotal = totalActiveStakeWei + required;
        uint256 cap = maxTotalStakeWei;
        if (cap != 0) {
            require(newTotal <= cap, "PWMStaking: total stake cap exceeded");
        }
        totalActiveStakeWei = newTotal;

        stakes[artifactHash] = Stake({
            staker: msg.sender,
            layer:  layer,
            amount: required,
            status: Status.Active
        });
        emit Staked(artifactHash, layer, msg.sender, required);
    }

    // ---------- resolution (governance-gated) ----------

    /// @notice Graduate a staked artifact: 50% back to staker, 50% seeds the supplied
    ///         benchmark's B-pool in PWMReward. For L3 stakes pass the artifact itself;
    ///         for L1/L2 the graduation caller nominates a child benchmark.
    function graduate(bytes32 artifactHash, bytes32 benchmarkHash) external onlyGovernance {
        Stake storage s = stakes[artifactHash];
        require(s.status == Status.Active, "PWMStaking: not active");
        require(address(reward) != address(0), "PWMStaking: reward unset");
        require(benchmarkHash != bytes32(0), "PWMStaking: zero benchmark");

        s.status = Status.Graduated;
        // CEI: decrement running total BEFORE any external call so a
        // re-entrant stake() cannot see stale totalActiveStakeWei.
        totalActiveStakeWei -= s.amount;
        uint256 half = s.amount / 2;
        uint256 other = s.amount - half;

        (bool ok, ) = payable(s.staker).call{value: half}("");
        require(ok, "PWMStaking: return failed");
        reward.seedBPool{value: other}(benchmarkHash);

        emit Graduated(artifactHash, s.staker, half, other);
    }

    /// @notice Uphold a challenge: 50% burned, 50% to challenger. Artifact delisted.
    function slashForChallenge(bytes32 artifactHash, address challenger) external onlyGovernance {
        Stake storage s = stakes[artifactHash];
        require(s.status == Status.Active, "PWMStaking: not active");
        require(challenger != address(0), "PWMStaking: zero challenger");

        s.status = Status.Slashed;
        totalActiveStakeWei -= s.amount;
        uint256 half = s.amount / 2;
        uint256 other = s.amount - half;

        (bool okBurn, ) = payable(BURN_SINK).call{value: half}("");
        require(okBurn, "PWMStaking: burn failed");
        (bool okCh, ) = payable(challenger).call{value: other}("");
        require(okCh, "PWMStaking: challenger transfer failed");

        emit ChallengeUpheld(artifactHash, challenger, half, other);
    }

    /// @notice Fraud: 100% burned. Artifact permanently delisted.
    function slashForFraud(bytes32 artifactHash) external onlyGovernance {
        Stake storage s = stakes[artifactHash];
        require(s.status == Status.Active, "PWMStaking: not active");

        s.status = Status.Fraud;
        totalActiveStakeWei -= s.amount;
        uint256 amt = s.amount;
        (bool ok, ) = payable(BURN_SINK).call{value: amt}("");
        require(ok, "PWMStaking: burn failed");

        emit FraudSlashed(artifactHash, amt);
    }

    // ---------- views ----------

    function stakeOf(bytes32 artifactHash)
        external
        view
        returns (address staker, uint8 layer, uint256 amount, Status status)
    {
        Stake storage s = stakes[artifactHash];
        return (s.staker, s.layer, s.amount, s.status);
    }
}
