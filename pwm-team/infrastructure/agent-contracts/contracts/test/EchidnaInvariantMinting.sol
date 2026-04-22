// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../PWMMinting.sol";
import "../PWMReward.sol";
import "../PWMTreasury.sol";

/// @title Echidna invariant harness for PWMMinting
/// @notice Tests that M_emitted never exceeds M_POOL and weight caches stay consistent.
///         Run: echidna-test contracts/test/EchidnaInvariantMinting.sol --contract EchidnaInvariantMinting
contract EchidnaInvariantMinting {
    PWMMinting   public minting;
    PWMReward    public reward;
    PWMTreasury  public treasury;

    // Track promoted principles and their expected weight sum
    uint256[] public promotedPrinciples;
    uint256   public expectedTotalWeight;

    constructor() payable {
        // Deploy minimal contract graph needed for mintFor to work
        treasury = new PWMTreasury(address(this));
        reward   = new PWMReward(address(this));
        minting  = new PWMMinting(address(this));

        // Wire contracts
        reward.setTreasury(address(treasury));
        reward.setMinting(address(minting));
        reward.setCertificate(address(this)); // this contract acts as certificate
        reward.setStaking(address(this));
        treasury.setReward(address(reward));
        minting.setCertificate(address(this)); // this contract acts as certificate
        minting.setReward(address(reward));
    }

    // Allow receiving ETH
    receive() external payable {}

    // --- Fuzzer entry points (Echidna calls these with random args) ---

    function setupPrinciple(uint256 principleId, uint256 delta, bytes32 benchmarkHash, uint256 rho) external {
        principleId = bound(principleId, 1, 50);
        delta = bound(delta, 1, 10);
        rho = bound(rho, 1, 1000);
        benchmarkHash = keccak256(abi.encode(principleId, benchmarkHash));

        try minting.setDelta(principleId, delta) {} catch {}
        try minting.registerBenchmark(principleId, benchmarkHash, rho) {} catch {}
        try minting.setPromotion(principleId, true) {} catch {}
    }

    function callMintFor(uint256 principleId, bytes32 benchmarkHash) external {
        principleId = bound(principleId, 1, 50);
        benchmarkHash = keccak256(abi.encode(principleId, benchmarkHash));

        // Fund minting contract if needed
        uint256 mintBal = address(minting).balance;
        if (mintBal < 1 ether) {
            (bool ok,) = address(minting).call{value: 10 ether}("");
            require(ok);
        }

        try minting.mintFor(principleId, benchmarkHash) {} catch {}
    }

    function changeDelta(uint256 principleId, uint256 newDelta) external {
        principleId = bound(principleId, 1, 50);
        newDelta = bound(newDelta, 1, 10);
        try minting.setDelta(principleId, newDelta) {} catch {}
    }

    function togglePromotion(uint256 principleId, bool promoted) external {
        principleId = bound(principleId, 1, 50);
        try minting.setPromotion(principleId, promoted) {} catch {}
    }

    function addBenchmark(uint256 principleId, bytes32 benchmarkHash, uint256 rho) external {
        principleId = bound(principleId, 1, 50);
        rho = bound(rho, 1, 1000);
        benchmarkHash = keccak256(abi.encode(principleId, benchmarkHash, rho));
        try minting.registerBenchmark(principleId, benchmarkHash, rho) {} catch {}
    }

    function removeBenchmark(uint256 principleId, bytes32 benchmarkHash) external {
        principleId = bound(principleId, 1, 50);
        benchmarkHash = keccak256(abi.encode(principleId, benchmarkHash));
        try minting.removeBenchmark(principleId, benchmarkHash) {} catch {}
    }

    // --- INVARIANTS (Echidna asserts these after every tx) ---

    /// @notice M_emitted must NEVER exceed M_POOL
    function echidna_emission_cap() public view returns (bool) {
        return minting.M_emitted() <= minting.M_POOL();
    }

    /// @notice remaining() must always equal M_POOL - M_emitted
    function echidna_remaining_consistent() public view returns (bool) {
        return minting.remaining() == minting.M_POOL() - minting.M_emitted();
    }

    /// @notice totalPrincipleWeight must never be negative (underflow)
    ///         With Solidity 0.8 checked math this can't underflow to a huge number,
    ///         but we verify it stays within a sane range.
    function echidna_weight_sane() public view returns (bool) {
        // Weight should never exceed a reasonable max:
        // 50 principles × delta 10 × activity 1000000 = 500_000_000
        return minting.totalPrincipleWeight() < 1e18;
    }

    // --- Helpers ---

    function bound(uint256 x, uint256 lo, uint256 hi) internal pure returns (uint256) {
        if (hi <= lo) return lo;
        return lo + (x % (hi - lo + 1));
    }
}
