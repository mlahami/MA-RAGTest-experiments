// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title PollCreator
 * @dev Permet la création et la gestion de multiples sondages dynamiques.
 */
contract PollCreator {
    
    struct Poll {
        string question;
        string[] options;
        uint256[] voteCounts;
        bool exists;
        bool isOpen;
        mapping(address => bool) hasVoted;
    }

    address public admin;
    uint256 public pollCount;
    mapping(uint256 => Poll) private polls;

    event PollCreated(uint256 indexed pollId, string question);
    event VoteRegistered(uint256 indexed pollId, address indexed voter, uint256 optionIndex);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Polls: Reserve a l'admin");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    /**
     * @dev Crée un nouveau sondage avec une question et une liste d'options.
     */
    function createPoll(string memory _question, string[] memory _options) public onlyAdmin {
        require(_options.length >= 2, "Polls: Il faut au moins 2 options");

        Poll storage newPoll = polls[pollCount];
        newPoll.question = _question;
        newPoll.options = _options;
        newPoll.voteCounts = new uint256[](_options.length);
        newPoll.exists = true;
        newPoll.isOpen = true;

        emit PollCreated(pollCount, _question);
        pollCount++;
    }

    /**
     * @dev Vote pour une option spécifique d'un sondage donné.
     */
    function vote(uint256 _pollId, uint256 _optionIndex) public {
        Poll storage poll = polls[_pollId];
        require(poll.exists, "Polls: Le sondage n'existe pas");
        require(poll.isOpen, "Polls: Le sondage est clos");
        require(!poll.hasVoted[msg.sender], "Polls: Vous avez deja vote");
        require(_optionIndex < poll.options.length, "Polls: Option invalide");

        poll.voteCounts[_optionIndex]++;
        poll.hasVoted[msg.sender] = true;

        emit VoteRegistered(_pollId, msg.sender, _optionIndex);
    }

    /**
     * @dev Récupère les détails et les résultats d'un sondage.
     */
    function getPollResults(uint256 _pollId) public view returns (
        string memory question, 
        string[] memory options, 
        uint256[] memory results
    ) {
        Poll storage poll = polls[_pollId];
        require(poll.exists, "Polls: Inexistant");
        return (poll.question, poll.options, poll.voteCounts);
    }

    /**
     * @dev Clôture un sondage.
     */
    function closePoll(uint256 _pollId) public onlyAdmin {
        polls[_pollId].isOpen = false;
    }
}