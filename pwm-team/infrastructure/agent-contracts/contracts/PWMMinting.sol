// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPWMReward {
    function depositMinting(bytes32 benchmarkHash) external payable;
}

/// @title PWMMinting
/// @notice Zeno emission over the fixed pool M_POOL = 17,220,000 PWM.
///         Each epoch emits `epochEmissionBps` of the remaining pool
///         (M_POOL − M_emitted), split across promoted principles by weight
///         w_k = δ_k × max(activity_k, 1). Emission flows into each
///         principle's designated benchmark pool in PWMReward.
///
/// M1.1 scope: per-principle emission (not per-benchmark sub-allocation).
/// Sub-principle (w_{k,j,b}) math is handled off-chain by agent-coord until a
/// later milestone pushes it on-chain.
contract PWMMinting {
    uint256 public constant M_POOL = 17_220_000 ether;
    uint16  public constant BPS_DENOM = 10_000;

    address public governance;
    address public certificate;
    IPWMReward public reward;

    uint256 public M_emitted;                 // cumulative PWM emitted
    uint256 public epochCooldown = 1 days;    // minimum seconds between epochEmit calls
    uint16  public epochEmissionBps = 100;    // 1.00% of remaining per epoch (default)
    uint256 public lastEmitAt;

    struct Principle {
        bool    promoted;
        uint256 delta;             // δ_k
        uint256 activity;          // cumulative events (activity_k)
        bytes32 benchmarkHash;     // designated benchmark pool for A_k inflow
    }
    mapping(uint256 => Principle) public principles;
    uint256[] public promotedIds;

    event GovernanceUpdated(address indexed newGovernance);
    event CertificateUpdated(address indexed newCertificate);
    event RewardUpdated(address indexed newReward);
    event PromotionSet(uint256 indexed principleId, bool promoted);
    event DeltaSet(uint256 indexed principleId, uint256 delta);
    event BenchmarkSet(uint256 indexed principleId, bytes32 benchmarkHash);
    event ActivityUpdated(uint256 indexed principleId, bytes32 indexed benchmarkHash, uint256 addedEvents, uint256 totalActivity);
    event EpochCooldownSet(uint256 secs);
    event EpochEmissionBpsSet(uint16 bps);
    event EpochEmitted(uint256 indexed epoch, uint256 totalEmitted, uint256 remainingAfter);
    event PrincipleEmission(uint256 indexed principleId, uint256 amount, bytes32 indexed benchmarkHash);

    modifier onlyGovernance()  { require(msg.sender == governance,  "PWMMinting: not governance");  _; }
    modifier onlyCertificate() { require(msg.sender == certificate, "PWMMinting: not certificate"); _; }

    constructor(address initialGovernance) {
        require(initialGovernance != address(0), "PWMMinting: zero governance");
        governance = initialGovernance;
    }

    // ---------- governance wiring ----------

    function setGovernance(address x) external onlyGovernance {
        require(x != address(0), "PWMMinting: zero governance");
        governance = x; emit GovernanceUpdated(x);
    }
    function setCertificate(address x) external onlyGovernance {
        require(x != address(0), "PWMMinting: zero certificate");
        certificate = x; emit CertificateUpdated(x);
    }
    function setReward(address x) external onlyGovernance {
        require(x != address(0), "PWMMinting: zero reward");
        reward = IPWMReward(x); emit RewardUpdated(x);
    }
    function setEpochCooldown(uint256 secs) external onlyGovernance {
        require(secs > 0, "PWMMinting: zero cooldown");
        epochCooldown = secs; emit EpochCooldownSet(secs);
    }
    function setEpochEmissionBps(uint16 bps) external onlyGovernance {
        require(bps > 0 && bps <= BPS_DENOM, "PWMMinting: bps out of range");
        epochEmissionBps = bps; emit EpochEmissionBpsSet(bps);
    }

    // ---------- principle management ----------

    function setPromotion(uint256 principleId, bool status) external onlyGovernance {
        Principle storage p = principles[principleId];
        if (status && !p.promoted) {
            require(p.benchmarkHash != bytes32(0), "PWMMinting: benchmark unset");
            require(p.delta > 0, "PWMMinting: delta unset");
            p.promoted = true;
            promotedIds.push(principleId);
        } else if (!status && p.promoted) {
            p.promoted = false;
            uint256 n = promotedIds.length;
            for (uint256 i = 0; i < n; i++) {
                if (promotedIds[i] == principleId) {
                    promotedIds[i] = promotedIds[n - 1];
                    promotedIds.pop();
                    break;
                }
            }
        }
        emit PromotionSet(principleId, status);
    }

    function setDelta(uint256 principleId, uint256 delta) external onlyGovernance {
        require(delta > 0, "PWMMinting: zero delta");
        principles[principleId].delta = delta;
        emit DeltaSet(principleId, delta);
    }

    function setPrincipleBenchmark(uint256 principleId, bytes32 benchmarkHash) external onlyGovernance {
        require(benchmarkHash != bytes32(0), "PWMMinting: zero benchmark");
        principles[principleId].benchmarkHash = benchmarkHash;
        emit BenchmarkSet(principleId, benchmarkHash);
    }

    // ---------- activity (called by PWMCertificate on finalize) ----------

    function updateActivity(uint256 principleId, bytes32 benchmarkHash, uint256 events) external onlyCertificate {
        principles[principleId].activity += events;
        emit ActivityUpdated(principleId, benchmarkHash, events, principles[principleId].activity);
    }

    // ---------- Zeno emission ----------

    function weightOf(uint256 principleId) public view returns (uint256) {
        Principle storage p = principles[principleId];
        if (!p.promoted) return 0;
        uint256 a = p.activity == 0 ? 1 : p.activity;
        return p.delta * a;
    }

    function remaining() public view returns (uint256) {
        return M_POOL - M_emitted;
    }

    function totalWeight() public view returns (uint256 sum) {
        uint256 n = promotedIds.length;
        for (uint256 i = 0; i < n; i++) sum += weightOf(promotedIds[i]);
    }

    /// @notice Emit this epoch's allocation to all promoted principles.
    ///         Requires the contract to be pre-funded with native PWM value.
    function epochEmit() external {
        require(block.timestamp >= lastEmitAt + epochCooldown, "PWMMinting: cooldown active");
        require(address(reward) != address(0), "PWMMinting: reward unset");
        require(promotedIds.length > 0, "PWMMinting: no promoted principles");

        uint256 rem = remaining();
        require(rem > 0, "PWMMinting: pool exhausted");

        uint256 budget = (rem * epochEmissionBps) / BPS_DENOM;
        require(budget > 0, "PWMMinting: budget zero");
        require(address(this).balance >= budget, "PWMMinting: underfunded");

        uint256 sumW = totalWeight();
        require(sumW > 0, "PWMMinting: zero total weight");

        lastEmitAt = block.timestamp;

        uint256 totalEmittedThisEpoch;
        uint256 n = promotedIds.length;
        for (uint256 i = 0; i < n; i++) {
            uint256 id = promotedIds[i];
            uint256 w = weightOf(id);
            if (w == 0) continue;
            uint256 amount = (budget * w) / sumW;
            if (amount == 0) continue;
            bytes32 bh = principles[id].benchmarkHash;
            reward.depositMinting{value: amount}(bh);
            totalEmittedThisEpoch += amount;
            emit PrincipleEmission(id, amount, bh);
        }

        M_emitted += totalEmittedThisEpoch;
        emit EpochEmitted(block.timestamp, totalEmittedThisEpoch, M_POOL - M_emitted);
    }

    receive() external payable {}

    function promotedCount() external view returns (uint256) { return promotedIds.length; }
}
