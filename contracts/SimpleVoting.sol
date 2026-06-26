// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleVoting
 * @dev Permet de voter "Oui" ou "Non" sur une proposition unique.
 */
contract SimpleVoting {
    
    struct Proposal {
        string description;
        uint256 voteCountYes;
        uint256 voteCountNo;
        bool isOpen;
    }

    Proposal public currentProposal;
    address public admin;

    // Mapping pour suivre qui a déjà voté
    mapping(address => bool) public hasVoted;

    event VoteCast(address indexed voter, bool choice);
    event ProposalClosed(uint256 finalYes, uint256 finalNo);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Voting: Reserve a l'administrateur");
        _;
    }

    modifier votingOpen() {
        require(currentProposal.isOpen, "Voting: Le vote est clos");
        _;
    }

    constructor(string memory _description) {
        admin = msg.sender;
        currentProposal = Proposal({
            description: _description,
            voteCountYes: 0,
            voteCountNo: 0,
            isOpen: true
        });
    }

    /**
     * @dev Enregistre un vote. 
     * @param _supportsProposal true pour "Oui", false pour "Non".
     */
    function vote(bool _supportsProposal) public votingOpen {
        require(!hasVoted[msg.sender], "Voting: Vous avez deja vote");

        if (_supportsProposal) {
            currentProposal.voteCountYes++;
        } else {
            currentProposal.voteCountNo++;
        }

        hasVoted[msg.sender] = true;
        emit VoteCast(msg.sender, _supportsProposal);
    }

    /**
     * @dev Ferme la session de vote.
     */
    function closeVoting() public onlyAdmin votingOpen {
        currentProposal.isOpen = false;
        emit ProposalClosed(currentProposal.voteCountYes, currentProposal.voteCountNo);
    }

    /**
     * @dev Retourne les résultats actuels.
     */
    function getResults() public view returns (uint256 yes, uint256 no) {
        return (currentProposal.voteCountYes, currentProposal.voteCountNo);
    }
}