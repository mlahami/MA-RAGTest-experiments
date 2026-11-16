// Benchmark candidate extracted from SolidityByExample/hacks: solidity-by-example.github.io/src/pages/hacks/front-running/PreventFrontRunning.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract SecuredFindThisHash {
    struct Commit {
        bytes32 solutionHash;
        uint256 commitTime;
        bool revealed;
    }
    bytes32 public hash =
        0x564ccaf7594d66b1eaaea24fe01f0585bf52ee70852af4eac0cc4b04711cd0e2;
    address public winner;
    uint256 public reward;
    bool public ended;
    mapping(address => Commit) commits;
    modifier gameActive() {
        require(!ended, "Already ended");
        _;
    }
    constructor() payable {
        reward = msg.value;
    }
    function commitSolution(bytes32 _solutionHash) public gameActive {
        Commit storage commit = commits[msg.sender];
        require(commit.commitTime == 0, "Already committed");
        commit.solutionHash = _solutionHash;
        commit.commitTime = block.timestamp;
        commit.revealed = false;
    }
    function getMySolution()
        public
        view
        gameActive
        returns (bytes32, uint256, bool)
    {
        Commit storage commit = commits[msg.sender];
        require(commit.commitTime != 0, "Not committed yet");
        return (commit.solutionHash, commit.commitTime, commit.revealed);
    }
    function revealSolution(string memory _solution, string memory _secret)
        public
        gameActive
    {
        Commit storage commit = commits[msg.sender];
        require(commit.commitTime != 0, "Not committed yet");
        require(
            commit.commitTime < block.timestamp,
            "Cannot reveal in the same block"
        );
        require(!commit.revealed, "Already committed and revealed");
        bytes32 solutionHash =
            keccak256(abi.encodePacked(msg.sender, _solution, _secret));
        require(solutionHash == commit.solutionHash, "Hash doesn't match");
        require(
            keccak256(abi.encodePacked(_solution)) == hash, "Incorrect answer"
        );
        winner = msg.sender;
        ended = true;
        (bool sent,) = payable(msg.sender).call{value: reward}("");
        if (!sent) {
            winner = address(0);
            ended = false;
            revert("Failed to send ether.");
        }
    }
}