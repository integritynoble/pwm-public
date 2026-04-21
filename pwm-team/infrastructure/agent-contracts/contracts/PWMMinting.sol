// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPWMReward {
    function depositMinting(bytes32 benchmarkHash) external payable;
}

/// @title PWMMinting
/// @notice Per-event Zeno emission, matching pwm_overview1.md §Per-Principle
///         Pool Allocation and §Spec and Benchmark Sub-Pool Allocation.
///
/// Principle weight (k level):
///     w_k        = δ_k × max(activity_k, 1)
///     activity_k = cumulative L4 solutions across all benchmarks under principle k
///                  (pwm_overview1.md specifies a 90-day rolling window; M1.1
///                   uses cumulative activity and flags the window as follow-up)
///
/// Benchmark weight (b level within principle k):
///     w_{k,j,b}  = ρ_{j,b} × max(activity_{k,j,b}, ρ_{j,b})
///     ρ_{j,b}    = 50 for P-benchmarks; {1, 3, 5, 10} for I-benchmarks
///
/// Per-event emission (fired by PWMCertificate.finalize just before distribute):
///     A_k        = (M_POOL - M_emitted) × w_k / Σ(w_j)
///     A_{k,j,b}  = A_k × w_{k,j,b} / Σ(w_{k,j',b'})
///
/// A_{k,j,b} is transferred into the benchmark's pool in PWMReward and then
/// drawn against by rank in the same finalize call. M_emitted increments by
/// exactly A_{k,j,b}; the pool asymptotes to zero without reaching it.
contract PWMMinting {
    uint256 public constant M_POOL = 17_220_000 ether;

    address public governance;
    address public certificate;
    IPWMReward public reward;

    uint256 public M_emitted;

    // ---- principle state ----
    struct Principle {
        bool     promoted;
        uint256  delta;           // δ_k
        uint256  activity;        // cumulative activity_k (all benchmarks)
        bytes32[] benchmarks;     // benchmarks owned by this principle (order-insensitive)
    }
    mapping(uint256 => Principle) private _principles;

    // ---- benchmark state (indexed by (principleId, benchmarkHash)) ----
    struct Benchmark {
        bool    registered;
        uint256 rho;              // ρ_{j,b}
        uint256 activity;         // activity_{k,j,b}
        uint256 index;            // position in Principle.benchmarks (for O(1) removal)
    }
    mapping(uint256 => mapping(bytes32 => Benchmark)) private _benchmarks;

    // ---- cached totals ----
    uint256 public totalPrincipleWeight;                          // Σ w_j
    mapping(uint256 => uint256) public sumBenchmarkWeight;        // Σ_{j',b'} w_{k,j',b'}

    event GovernanceUpdated(address indexed newGovernance);
    event CertificateUpdated(address indexed newCertificate);
    event RewardUpdated(address indexed newReward);

    event PromotionSet(uint256 indexed principleId, bool promoted);
    event DeltaSet(uint256 indexed principleId, uint256 delta);
    event BenchmarkRegistered(uint256 indexed principleId, bytes32 indexed benchmarkHash, uint256 rho);
    event BenchmarkRhoUpdated(uint256 indexed principleId, bytes32 indexed benchmarkHash, uint256 rho);
    event BenchmarkRemoved(uint256 indexed principleId, bytes32 indexed benchmarkHash);
    event ActivityRecorded(
        uint256 indexed principleId,
        bytes32 indexed benchmarkHash,
        uint256 principleActivity,
        uint256 benchmarkActivity
    );
    event Minted(
        uint256 indexed principleId,
        bytes32 indexed benchmarkHash,
        uint256 A_k,
        uint256 A_kjb,
        uint256 remainingAfter
    );

    modifier onlyGovernance()  { require(msg.sender == governance,  "PWMMinting: not governance");  _; }
    modifier onlyCertificate() { require(msg.sender == certificate, "PWMMinting: not certificate"); _; }

    constructor(address initialGovernance) {
        require(initialGovernance != address(0), "PWMMinting: zero governance");
        governance = initialGovernance;
    }

    // ---------- wiring ----------

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

    // ---------- principle management ----------

    function setDelta(uint256 principleId, uint256 delta) external onlyGovernance {
        require(delta > 0, "PWMMinting: zero delta");
        Principle storage p = _principles[principleId];
        uint256 oldW = _principleWeight(principleId);
        p.delta = delta;
        uint256 newW = _principleWeight(principleId);
        if (p.promoted) {
            totalPrincipleWeight = totalPrincipleWeight - oldW + newW;
        }
        emit DeltaSet(principleId, delta);
    }

    function setPromotion(uint256 principleId, bool status) external onlyGovernance {
        Principle storage p = _principles[principleId];
        if (status && !p.promoted) {
            require(p.delta > 0, "PWMMinting: delta unset");
            require(p.benchmarks.length > 0, "PWMMinting: no benchmarks");
            p.promoted = true;
            totalPrincipleWeight += _principleWeight(principleId);
        } else if (!status && p.promoted) {
            totalPrincipleWeight -= _principleWeight(principleId);
            p.promoted = false;
        }
        emit PromotionSet(principleId, status);
    }

    function registerBenchmark(uint256 principleId, bytes32 benchmarkHash, uint256 rho) external onlyGovernance {
        require(benchmarkHash != bytes32(0), "PWMMinting: zero benchmark");
        require(rho > 0, "PWMMinting: zero rho");
        Principle storage p = _principles[principleId];
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        require(!b.registered, "PWMMinting: already registered");

        b.registered = true;
        b.rho = rho;
        b.index = p.benchmarks.length;
        p.benchmarks.push(benchmarkHash);

        sumBenchmarkWeight[principleId] += _benchmarkWeight(principleId, benchmarkHash);
        emit BenchmarkRegistered(principleId, benchmarkHash, rho);
    }

    function setBenchmarkRho(uint256 principleId, bytes32 benchmarkHash, uint256 rho) external onlyGovernance {
        require(rho > 0, "PWMMinting: zero rho");
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        require(b.registered, "PWMMinting: unknown benchmark");
        uint256 oldW = _benchmarkWeight(principleId, benchmarkHash);
        b.rho = rho;
        uint256 newW = _benchmarkWeight(principleId, benchmarkHash);
        sumBenchmarkWeight[principleId] = sumBenchmarkWeight[principleId] - oldW + newW;
        emit BenchmarkRhoUpdated(principleId, benchmarkHash, rho);
    }

    function removeBenchmark(uint256 principleId, bytes32 benchmarkHash) external onlyGovernance {
        Principle storage p = _principles[principleId];
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        require(b.registered, "PWMMinting: unknown benchmark");
        // do not allow removal while promoted with this being the only benchmark
        if (p.promoted) {
            require(p.benchmarks.length > 1, "PWMMinting: cannot leave zero benchmarks");
        }
        sumBenchmarkWeight[principleId] -= _benchmarkWeight(principleId, benchmarkHash);

        // swap-and-pop removal from the array
        uint256 idx = b.index;
        uint256 last = p.benchmarks.length - 1;
        if (idx != last) {
            bytes32 moved = p.benchmarks[last];
            p.benchmarks[idx] = moved;
            _benchmarks[principleId][moved].index = idx;
        }
        p.benchmarks.pop();
        delete _benchmarks[principleId][benchmarkHash];

        emit BenchmarkRemoved(principleId, benchmarkHash);
    }

    // ---------- per-event mint (called by PWMCertificate.finalize) ----------

    /// @notice Compute A_{k,j,b} for the current mining event and deposit into
    ///         the benchmark's pool. Increments activity_k and activity_{k,j,b}
    ///         after emission so the first event for a fresh principle uses
    ///         w_k = δ_k × 1 (the genesis equal-share case).
    function mintFor(uint256 principleId, bytes32 benchmarkHash)
        external
        onlyCertificate
        returns (uint256 A_kjb)
    {
        Principle storage p = _principles[principleId];
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        require(p.promoted, "PWMMinting: not promoted");
        require(b.registered, "PWMMinting: unknown benchmark");
        require(address(reward) != address(0), "PWMMinting: reward unset");

        uint256 rem = remaining();
        uint256 sumW = totalPrincipleWeight;
        uint256 wK   = _principleWeight(principleId);

        uint256 A_k = 0;
        if (rem > 0 && sumW > 0 && wK > 0) {
            A_k = (rem * wK) / sumW;
        }

        uint256 sumBW = sumBenchmarkWeight[principleId];
        uint256 wB    = _benchmarkWeight(principleId, benchmarkHash);
        if (A_k > 0 && sumBW > 0 && wB > 0) {
            A_kjb = (A_k * wB) / sumBW;
        }

        if (A_kjb > 0) {
            require(address(this).balance >= A_kjb, "PWMMinting: underfunded");
            M_emitted += A_kjb;
        }

        // CEI: update all state before external calls.
        _incrementActivity(principleId, benchmarkHash);

        emit Minted(principleId, benchmarkHash, A_k, A_kjb, M_POOL - M_emitted);

        // Interaction last — external call after all state updates.
        if (A_kjb > 0) {
            reward.depositMinting{value: A_kjb}(benchmarkHash);
        }
    }

    function _incrementActivity(uint256 principleId, bytes32 benchmarkHash) internal {
        Principle storage p = _principles[principleId];
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];

        uint256 oldBW = _benchmarkWeight(principleId, benchmarkHash);
        uint256 oldPW = _principleWeight(principleId);

        p.activity += 1;
        b.activity += 1;

        uint256 newBW = _benchmarkWeight(principleId, benchmarkHash);
        sumBenchmarkWeight[principleId] = sumBenchmarkWeight[principleId] - oldBW + newBW;

        if (p.promoted) {
            uint256 newPW = _principleWeight(principleId);
            totalPrincipleWeight = totalPrincipleWeight - oldPW + newPW;
        }

        emit ActivityRecorded(principleId, benchmarkHash, p.activity, b.activity);
    }

    // ---------- views ----------

    function remaining() public view returns (uint256) {
        return M_POOL - M_emitted;
    }

    function principleOf(uint256 principleId)
        external view
        returns (bool promoted, uint256 delta, uint256 activity, uint256 numBenchmarks)
    {
        Principle storage p = _principles[principleId];
        return (p.promoted, p.delta, p.activity, p.benchmarks.length);
    }

    function benchmarkOf(uint256 principleId, bytes32 benchmarkHash)
        external view
        returns (bool registered, uint256 rho, uint256 activity)
    {
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        return (b.registered, b.rho, b.activity);
    }

    function principleWeight(uint256 principleId) external view returns (uint256) {
        if (!_principles[principleId].promoted) return 0;
        return _principleWeight(principleId);
    }

    function benchmarkWeight(uint256 principleId, bytes32 benchmarkHash) external view returns (uint256) {
        if (!_benchmarks[principleId][benchmarkHash].registered) return 0;
        return _benchmarkWeight(principleId, benchmarkHash);
    }

    function _principleWeight(uint256 principleId) internal view returns (uint256) {
        Principle storage p = _principles[principleId];
        uint256 a = p.activity == 0 ? 1 : p.activity;
        return p.delta * a;
    }

    function _benchmarkWeight(uint256 principleId, bytes32 benchmarkHash) internal view returns (uint256) {
        Benchmark storage b = _benchmarks[principleId][benchmarkHash];
        uint256 a = b.activity < b.rho ? b.rho : b.activity;
        return b.rho * a;
    }

    receive() external payable {}
}
