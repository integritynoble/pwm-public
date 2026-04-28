// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPWMStaking {
    function stake(uint8 layer, bytes32 artifactHash) external payable;
}

/// @title MaliciousReceiver
/// @notice Test-only contract that stakes via PWMStaking but reverts when ETH
///         is sent back to it. Used to exercise the `require(ok)` branches
///         in `graduate()` and `slashForChallenge()`.
/// @dev    NOT part of the production deployment. Lives under `contracts/test/`
///         alongside the Echidna invariant harnesses; coverage tooling reports
///         these test contracts at 0% coverage and that is by design.
contract MaliciousReceiver {
    bool public rejecting = true;

    function setRejecting(bool v) external { rejecting = v; }

    function stakeOn(IPWMStaking staking, uint8 layer, bytes32 hash)
        external payable
    {
        staking.stake{value: msg.value}(layer, hash);
    }

    receive() external payable {
        if (rejecting) revert("MaliciousReceiver: reject");
    }
}
