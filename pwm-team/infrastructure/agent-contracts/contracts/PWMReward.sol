// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPWMTreasury {
    function receive15pct(uint256 principleId, uint256 amount) external payable;
}

/// @title PWMReward
/// @notice Holds the per-benchmark reward pool and settles ranked-draw payouts
///         triggered by PWMCertificate.finalize().
///
/// Ranked draw (of the current pool balance at settle time):
///   Rank 1 = 40%, Rank 2 = 5%, Rank 3 = 2%, Ranks 4-10 = 1% each (total paid 54%).
///   Rank 11+ = no draw — the share rolls over inside the pool.
///
/// Split of the drawn amount D:
///   AC (action credit)  : D × p × 55%
///   CP (compute provider): D × (1-p) × 55%
///   L3 benchmark creator: D × 15%
///   L2 spec creator     : D × 10%
///   L1 principle creator: D × 5%
///   T_k treasury        : D × 15%
///   (total = 100% of D)
///
/// Values are routed in native coin for M1.1; ERC20 PWM swap-in is a future migration.
contract PWMReward {
    uint16 public constant BPS_DENOM      = 10_000;
    uint16 public constant SPLIT_AC_CP    = 5_500; // combined AC+CP share of D, in bps
    uint16 public constant SPLIT_L3       = 1_500;
    uint16 public constant SPLIT_L2       = 1_000;
    uint16 public constant SPLIT_L1       =   500;
    uint16 public constant SPLIT_TREASURY = 1_500;
    uint8  public constant MAX_RANK       = 10;

    address public governance;
    address public certificate; // PWMCertificate is the only caller of distribute()
    address public minting;     // PWMMinting is the only caller of depositMinting()
    address public staking;     // PWMStaking is the only caller of seedBPool() (from promotions)
    IPWMTreasury public treasury;

    mapping(bytes32 => uint256) public pool; // benchmarkHash => PWM balance
    mapping(bytes32 => bool)    public settled; // certHash => already distributed?

    struct Draw {
        bytes32 benchmarkHash;
        uint256 principleId;
        address l1Creator;
        address l2Creator;
        address l3Creator;
        address acWallet;
        address cpWallet;
        uint16  shareRatioP; // p × 10000, 1000..9000
        uint8   rank;        // 1..MAX_RANK, else no-op
    }

    event PoolSeeded(bytes32 indexed benchmarkHash, uint256 amount, uint256 newBalance, address indexed from, string kind);
    event DrawSettled(
        bytes32 indexed certHash,
        bytes32 indexed benchmarkHash,
        uint8           rank,
        uint256         drawAmount,
        uint256         rolloverRemaining
    );
    event RoyaltiesPaid(bytes32 indexed certHash, address ac, uint256 acAmt, address cp, uint256 cpAmt, uint256 treasuryAmt);
    event GovernanceUpdated(address indexed newGovernance);
    event CertificateUpdated(address indexed newCertificate);
    event MintingUpdated(address indexed newMinting);
    event StakingUpdated(address indexed newStaking);
    event TreasuryUpdated(address indexed newTreasury);

    modifier onlyGovernance() { require(msg.sender == governance, "PWMReward: not governance"); _; }
    modifier onlyCertificate() { require(msg.sender == certificate, "PWMReward: not certificate"); _; }

    constructor(address initialGovernance) {
        require(initialGovernance != address(0), "PWMReward: zero governance");
        governance = initialGovernance;
    }

    // ---------- governance wiring ----------

    function setGovernance(address x) external onlyGovernance {
        require(x != address(0), "PWMReward: zero governance");
        governance = x;
        emit GovernanceUpdated(x);
    }
    function setCertificate(address x) external onlyGovernance {
        require(x != address(0), "PWMReward: zero certificate");
        certificate = x;
        emit CertificateUpdated(x);
    }
    function setMinting(address x) external onlyGovernance {
        require(x != address(0), "PWMReward: zero minting");
        minting = x;
        emit MintingUpdated(x);
    }
    function setStaking(address x) external onlyGovernance {
        require(x != address(0), "PWMReward: zero staking");
        staking = x;
        emit StakingUpdated(x);
    }
    function setTreasury(address x) external onlyGovernance {
        require(x != address(0), "PWMReward: zero treasury");
        treasury = IPWMTreasury(x);
        emit TreasuryUpdated(x);
    }

    // ---------- pool inflows ----------

    /// @notice B-pool seed from a successful promotion (called by PWMStaking).
    function seedBPool(bytes32 benchmarkHash) external payable {
        require(msg.sender == staking, "PWMReward: not staking");
        _credit(benchmarkHash, msg.value, "B-pool-seed");
    }

    /// @notice Protocol minting deposit (called by PWMMinting).
    function depositMinting(bytes32 benchmarkHash) external payable {
        require(msg.sender == minting, "PWMReward: not minting");
        _credit(benchmarkHash, msg.value, "A-pool-minting");
    }

    /// @notice Direct contributor bounty (B_k) — any caller, any time.
    function depositBounty(bytes32 benchmarkHash) external payable {
        _credit(benchmarkHash, msg.value, "B-pool-bounty");
    }

    function _credit(bytes32 benchmarkHash, uint256 amount, string memory kind) internal {
        require(benchmarkHash != bytes32(0), "PWMReward: zero benchmark");
        require(amount > 0, "PWMReward: zero amount");
        pool[benchmarkHash] += amount;
        emit PoolSeeded(benchmarkHash, amount, pool[benchmarkHash], msg.sender, kind);
    }

    // ---------- settlement ----------

    /// @notice Compute the rank's share of the pool in bps. 11+ returns 0 (rollover).
    function rankBps(uint8 rank) public pure returns (uint16) {
        if (rank == 1) return 4_000;
        if (rank == 2) return 500;
        if (rank == 3) return 200;
        if (rank >= 4 && rank <= MAX_RANK) return 100;
        return 0;
    }

    /// @notice Settle a certificate's ranked draw. Only PWMCertificate may call.
    function distribute(bytes32 certHash, Draw calldata d) external onlyCertificate {
        require(!settled[certHash], "PWMReward: already settled");
        require(d.shareRatioP >= 1000 && d.shareRatioP <= 9000, "PWMReward: p out of range");
        require(d.acWallet != address(0) && d.cpWallet != address(0), "PWMReward: zero AC/CP");
        require(d.l1Creator != address(0) && d.l2Creator != address(0) && d.l3Creator != address(0),
                "PWMReward: zero creator");
        require(address(treasury) != address(0), "PWMReward: treasury unset");

        settled[certHash] = true;

        uint16 rbps = rankBps(d.rank);
        if (rbps == 0) {
            // rollover: nothing drawn; amount stays in pool
            emit DrawSettled(certHash, d.benchmarkHash, d.rank, 0, pool[d.benchmarkHash]);
            return;
        }

        uint256 balance = pool[d.benchmarkHash];
        uint256 drawAmt = (balance * rbps) / BPS_DENOM;
        if (drawAmt == 0) {
            emit DrawSettled(certHash, d.benchmarkHash, d.rank, 0, balance);
            return;
        }

        pool[d.benchmarkHash] = balance - drawAmt;

        // Split drawAmt into six buckets.
        uint256 acAmt = (drawAmt * uint256(d.shareRatioP) * SPLIT_AC_CP) / (uint256(BPS_DENOM) * BPS_DENOM);
        uint256 cpAmt = (drawAmt * (BPS_DENOM - uint256(d.shareRatioP)) * SPLIT_AC_CP) / (uint256(BPS_DENOM) * BPS_DENOM);
        uint256 l3Amt = (drawAmt * SPLIT_L3) / BPS_DENOM;
        uint256 l2Amt = (drawAmt * SPLIT_L2) / BPS_DENOM;
        uint256 l1Amt = (drawAmt * SPLIT_L1) / BPS_DENOM;
        // Treasury takes the remainder (absorbs any integer-division dust) so
        // the 6 buckets always sum to exactly drawAmt.
        uint256 tkAmt = drawAmt - acAmt - cpAmt - l3Amt - l2Amt - l1Amt;

        _send(d.acWallet, acAmt);
        _send(d.cpWallet, cpAmt);
        _send(d.l3Creator, l3Amt);
        _send(d.l2Creator, l2Amt);
        _send(d.l1Creator, l1Amt);
        treasury.receive15pct{value: tkAmt}(d.principleId, tkAmt);

        emit RoyaltiesPaid(certHash, d.acWallet, acAmt, d.cpWallet, cpAmt, tkAmt);
        emit DrawSettled(certHash, d.benchmarkHash, d.rank, drawAmt, pool[d.benchmarkHash]);
    }

    function _send(address to, uint256 amount) internal {
        if (amount == 0) return;
        (bool ok, ) = payable(to).call{value: amount}("");
        require(ok, "PWMReward: transfer failed");
    }

    /// @notice Current pool balance for a benchmark.
    function poolOf(bytes32 benchmarkHash) external view returns (uint256) {
        return pool[benchmarkHash];
    }
}
