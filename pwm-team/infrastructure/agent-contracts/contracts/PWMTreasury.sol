// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PWMTreasury
/// @notice Per-principle treasury (T_k). Each principle is self-funded:
///         accumulates 15% of every L4 minting draw under that principle and
///         pays out M4 adversarial bounties (cap: 50% of current T_k).
///         There is no global treasury.
contract PWMTreasury {
    address public governance; // may change authorised callers + pay bounties
    address public reward;     // PWMReward — the only contract that can fund T_k

    mapping(uint256 => uint256) public treasury; // principleId => PWM balance

    event FundsReceived(uint256 indexed principleId, uint256 amount, uint256 newBalance);
    event BountyPaid(uint256 indexed principleId, address indexed winner, uint256 amount, uint256 newBalance);
    event GovernanceUpdated(address indexed newGovernance);
    event RewardUpdated(address indexed newReward);

    modifier onlyGovernance() {
        require(msg.sender == governance, "PWMTreasury: not governance");
        _;
    }

    modifier onlyReward() {
        require(msg.sender == reward, "PWMTreasury: not reward");
        _;
    }

    constructor(address initialGovernance) {
        require(initialGovernance != address(0), "PWMTreasury: zero governance");
        governance = initialGovernance;
    }

    function setGovernance(address newGovernance) external onlyGovernance {
        require(newGovernance != address(0), "PWMTreasury: zero governance");
        governance = newGovernance;
        emit GovernanceUpdated(newGovernance);
    }

    function setReward(address newReward) external onlyGovernance {
        require(newReward != address(0), "PWMTreasury: zero reward");
        reward = newReward;
        emit RewardUpdated(newReward);
    }

    /// @notice Credit T_k with the 15% cut from a completed L4 draw. Accepts native value.
    function receive15pct(uint256 principleId, uint256 amount) external payable onlyReward {
        require(msg.value == amount, "PWMTreasury: value mismatch");
        treasury[principleId] += amount;
        emit FundsReceived(principleId, amount, treasury[principleId]);
    }

    /// @notice Pay an M4 adversarial bounty to `winner`, capped at 50% of T_k.
    function payAdversarialBounty(uint256 principleId, address winner, uint256 amount)
        external
        onlyGovernance
    {
        require(winner != address(0), "PWMTreasury: zero winner");
        uint256 balance = treasury[principleId];
        require(amount > 0, "PWMTreasury: zero amount");
        require(amount <= balance, "PWMTreasury: exceeds balance");
        require(amount * 2 <= balance, "PWMTreasury: exceeds 50% cap");

        treasury[principleId] = balance - amount;
        (bool ok, ) = payable(winner).call{value: amount}("");
        require(ok, "PWMTreasury: transfer failed");

        emit BountyPaid(principleId, winner, amount, treasury[principleId]);
    }

    /// @notice Returns T_k balance for a principle.
    function balanceOf(uint256 principleId) external view returns (uint256) {
        return treasury[principleId];
    }
}
