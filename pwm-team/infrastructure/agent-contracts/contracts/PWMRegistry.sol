// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PWMRegistry — Immutable artifact hash store
/// @notice Stores L1/L2/L3/L4 artifact hashes. Append-only. No delete, no update.
contract PWMRegistry {
    struct Artifact {
        bytes32 parentHash;
        uint8   layer;          // 1=Principle, 2=Spec, 3=Benchmark, 4=Solution
        address creator;
        uint256 timestamp;
    }

    mapping(bytes32 => Artifact) private _artifacts;

    event ArtifactRegistered(
        bytes32 indexed hash,
        uint8   layer,
        address indexed creator,
        uint256 timestamp
    );

    /// @notice Register a new artifact. Reverts if hash already exists.
    function register(
        bytes32 hash,
        bytes32 parentHash,
        uint8   layer,
        address creator
    ) external {
        require(_artifacts[hash].timestamp == 0, "PWMRegistry: already registered");
        require(layer >= 1 && layer <= 4, "PWMRegistry: invalid layer");
        // TODO: access control — only authorised callers (PWMStaking, PWMCertificate)
        _artifacts[hash] = Artifact(parentHash, layer, creator, block.timestamp);
        emit ArtifactRegistered(hash, layer, creator, block.timestamp);
    }

    /// @notice Retrieve artifact metadata.
    function getArtifact(bytes32 hash)
        external view
        returns (bytes32 parentHash, uint8 layer, address creator, uint256 timestamp)
    {
        Artifact memory a = _artifacts[hash];
        return (a.parentHash, a.layer, a.creator, a.timestamp);
    }

    /// @notice Returns true if hash is registered.
    function exists(bytes32 hash) external view returns (bool) {
        return _artifacts[hash].timestamp != 0;
    }
}
