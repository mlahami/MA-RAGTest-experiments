// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MultisigWallet {
    uint256 public constant TIMELOCK_DELAY = 2 days;

    struct Transaction {
        address to;
        uint256 value;
        bytes data;
        bool executed;
        bool cancelled;
        uint256 confirmations;
        uint256 createdAt;
    }

    address[] public signers;
    mapping(address => bool) public isSigner;
    mapping(uint256 => mapping(address => bool)) public confirmed;
    Transaction[] public transactions;

    uint256 public quorum;
    bool private _locked;

    event Deposit(address indexed sender, uint256 amount);
    event Proposed(uint256 indexed txId, address indexed to, uint256 value, bytes data);
    event Confirmed(uint256 indexed txId, address indexed signer);
    event Revoked(uint256 indexed txId, address indexed signer);
    event Executed(uint256 indexed txId);
    event Cancelled(uint256 indexed txId);
    event SignerAdded(address indexed signer);
    event SignerRemoved(address indexed signer);
    event QuorumChanged(uint256 newQuorum);

    modifier onlyThis() { require(msg.sender == address(this), "Only via multisig"); _; }
    modifier onlySigner() { require(isSigner[msg.sender], "Not a signer"); _; }
    modifier txExists(uint256 id) { require(id < transactions.length, "Tx not found"); _; }
    modifier notExecuted(uint256 id) { require(!transactions[id].executed, "Already executed"); _; }
    modifier notCancelled(uint256 id) { require(!transactions[id].cancelled, "Cancelled"); _; }
    modifier noReentrant() { require(!_locked, "Reentrant"); _locked = true; _; _locked = false; }

    constructor(address[] memory _signers, uint256 _quorum) {
        require(_signers.length >= _quorum && _quorum > 0, "Invalid quorum");
        for (uint i = 0; i < _signers.length; i++) {
            require(_signers[i] != address(0) && !isSigner[_signers[i]], "Invalid signer");
            isSigner[_signers[i]] = true;
            signers.push(_signers[i]);
        }
        quorum = _quorum;
    }

    receive() external payable { emit Deposit(msg.sender, msg.value); }

    function propose(address to, uint256 value, bytes calldata data)
        external onlySigner returns (uint256)
    {
        require(to != address(0), "Zero address");
        uint256 id = transactions.length;
        transactions.push(Transaction({
            to: to, value: value, data: data,
            executed: false, cancelled: false,
            confirmations: 0, createdAt: block.timestamp
        }));
        emit Proposed(id, to, value, data);
        return id;
    }

    function confirm(uint256 id)
        external onlySigner txExists(id) notExecuted(id) notCancelled(id)
    {
        require(!confirmed[id][msg.sender], "Already confirmed");
        confirmed[id][msg.sender] = true;
        transactions[id].confirmations++;
        emit Confirmed(id, msg.sender);
    }

    function revoke(uint256 id)
        external onlySigner txExists(id) notExecuted(id) notCancelled(id)
    {
        require(confirmed[id][msg.sender], "Not confirmed");
        confirmed[id][msg.sender] = false;
        transactions[id].confirmations--;
        emit Revoked(id, msg.sender);
    }

    function execute(uint256 id)
        external noReentrant onlySigner txExists(id) notExecuted(id) notCancelled(id)
    {
        Transaction storage tx_ = transactions[id];
        require(tx_.confirmations >= quorum, "Quorum not reached");
        require(block.timestamp >= tx_.createdAt + TIMELOCK_DELAY, "Timelock active");
        require(address(this).balance >= tx_.value, "Insufficient funds");
        tx_.executed = true;
        (bool success,) = tx_.to.call{value: tx_.value}(tx_.data);
        require(success, "Execution failed");
        emit Executed(id);
    }

    function cancel(uint256 id)
        external onlyThis txExists(id) notExecuted(id) notCancelled(id)
    {
        transactions[id].cancelled = true;
        emit Cancelled(id);
    }

    function addSigner(address signer) external onlyThis {
        require(!isSigner[signer] && signer != address(0), "Invalid");
        isSigner[signer] = true;
        signers.push(signer);
        emit SignerAdded(signer);
    }

    function removeSigner(address signer) external onlyThis {
        require(isSigner[signer], "Not a signer");
        require(signers.length - 1 >= quorum, "Would break quorum");
        isSigner[signer] = false;
        for (uint i = 0; i < signers.length; i++) {
            if (signers[i] == signer) {
                signers[i] = signers[signers.length - 1];
                signers.pop();
                break;
            }
        }
        emit SignerRemoved(signer);
    }

    function setQuorum(uint256 _quorum) external onlyThis {
        require(_quorum > 0 && _quorum <= signers.length, "Invalid quorum");
        quorum = _quorum;
        emit QuorumChanged(_quorum);
    }

    function getTransactionCount() external view returns (uint256) { return transactions.length; }
    function getSigners() external view returns (address[] memory) { return signers; }
}