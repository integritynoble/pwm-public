// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PWMGovernance
/// @notice Phase 1-2: 3-of-5 multisig over the 5 founder wallets. Proposes and
///         confirms parameter changes behind a 48-hour time-lock. activateDAO()
///         is a one-way switch that disables the multisig path forever; the
///         DAO voting implementation itself is deferred (post-M3 per roadmap).
contract PWMGovernance {
    uint256 public constant REQUIRED_APPROVALS = 3;
    uint256 public constant NUM_FOUNDERS       = 5;
    uint256 public constant TIME_LOCK          = 48 hours;

    address[NUM_FOUNDERS] public founders;
    mapping(address => bool) public isFounder;

    mapping(bytes32 => uint256) public parameters; // key => current value

    struct Proposal {
        bytes32 key;
        uint256 value;
        uint256 proposedAt;    // 0 once executed/cancelled
        uint8   approvals;     // count of yeses
        bool    executed;
        bool    cancelled;
    }
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public approved; // proposalId => founder => yes?
    uint256 public nextProposalId;

    bool public daoActivated;

    event ProposalCreated(uint256 indexed id, bytes32 indexed key, uint256 value, address indexed proposer);
    event ProposalApproved(uint256 indexed id, address indexed founder, uint8 approvals);
    event ProposalExecuted(uint256 indexed id, bytes32 indexed key, uint256 value);
    event ProposalCancelled(uint256 indexed id);
    event DAOActivated(uint256 at);

    modifier onlyFounder() {
        require(isFounder[msg.sender], "PWMGovernance: not founder");
        _;
    }

    modifier multisigActive() {
        require(!daoActivated, "PWMGovernance: DAO active, multisig disabled");
        _;
    }

    constructor(address[NUM_FOUNDERS] memory _founders) {
        for (uint256 i = 0; i < NUM_FOUNDERS; i++) {
            require(_founders[i] != address(0), "PWMGovernance: zero founder");
            require(!isFounder[_founders[i]], "PWMGovernance: duplicate founder");
            founders[i] = _founders[i];
            isFounder[_founders[i]] = true;
        }
    }

    /// @notice Propose a parameter change. 48h timelock starts now.
    function proposeParameter(bytes32 key, uint256 value)
        external
        onlyFounder
        multisigActive
        returns (uint256 id)
    {
        id = nextProposalId++;
        proposals[id] = Proposal({
            key:        key,
            value:      value,
            proposedAt: block.timestamp,
            approvals:  1,
            executed:   false,
            cancelled:  false
        });
        approved[id][msg.sender] = true;
        emit ProposalCreated(id, key, value, msg.sender);
        emit ProposalApproved(id, msg.sender, 1);
    }

    /// @notice Approve a pending proposal (one vote per founder).
    function approveProposal(uint256 id) external onlyFounder multisigActive {
        Proposal storage p = proposals[id];
        require(p.proposedAt != 0, "PWMGovernance: unknown proposal");
        require(!p.executed && !p.cancelled, "PWMGovernance: finalised");
        require(!approved[id][msg.sender], "PWMGovernance: already approved");
        approved[id][msg.sender] = true;
        p.approvals += 1;
        emit ProposalApproved(id, msg.sender, p.approvals);
    }

    /// @notice Execute an approved proposal after the timelock elapses.
    function executeProposal(uint256 id) external onlyFounder multisigActive {
        Proposal storage p = proposals[id];
        require(p.proposedAt != 0, "PWMGovernance: unknown proposal");
        require(!p.executed && !p.cancelled, "PWMGovernance: finalised");
        require(p.approvals >= REQUIRED_APPROVALS, "PWMGovernance: insufficient approvals");
        require(block.timestamp >= p.proposedAt + TIME_LOCK, "PWMGovernance: timelock not elapsed");

        p.executed = true;
        parameters[p.key] = p.value;
        emit ProposalExecuted(id, p.key, p.value);
    }

    /// @notice Any founder may cancel a pending proposal (e.g., if values are wrong).
    function cancelProposal(uint256 id) external onlyFounder multisigActive {
        Proposal storage p = proposals[id];
        require(p.proposedAt != 0, "PWMGovernance: unknown proposal");
        require(!p.executed && !p.cancelled, "PWMGovernance: finalised");
        p.cancelled = true;
        emit ProposalCancelled(id);
    }

    /// @notice Irreversible: transition to DAO voting. Requires 3-of-5 confirmation
    ///         via the same approval flow (here implemented as a dedicated entry point).
    ///         The DAO implementation itself is out-of-scope for M1.1; callers check
    ///         `daoActivated` and switch over the parameter-setting authority off-chain.
    function activateDAO(uint256 id) external onlyFounder multisigActive {
        Proposal storage p = proposals[id];
        require(p.proposedAt != 0, "PWMGovernance: unknown proposal");
        require(!p.executed && !p.cancelled, "PWMGovernance: finalised");
        require(p.key == keccak256("ACTIVATE_DAO"), "PWMGovernance: wrong proposal key");
        require(p.approvals >= REQUIRED_APPROVALS, "PWMGovernance: insufficient approvals");
        require(block.timestamp >= p.proposedAt + TIME_LOCK, "PWMGovernance: timelock not elapsed");

        p.executed = true;
        daoActivated = true;
        emit DAOActivated(block.timestamp);
    }

    /// @notice Read a parameter value (0 if unset).
    function getParameter(bytes32 key) external view returns (uint256) {
        return parameters[key];
    }
}
