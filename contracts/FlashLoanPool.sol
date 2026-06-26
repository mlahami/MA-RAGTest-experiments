// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFlashLoanReceiver {
    function onFlashLoan(
        address initiator,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32);
}

contract FlashLoanPool {
    bytes32 public constant CALLBACK_SUCCESS = keccak256("EIP3156FlashBorrower.onFlashLoan");
    uint256 public constant MAX_FEE_BPS = 500;   // 5% max fee
    uint256 public constant BPS = 10000;
    uint256 public constant MAX_LOAN_PERCENT = 5000; // 50% of pool per loan

    address public owner;
    uint256 public feeBps = 9;       // 0.09% default (Aave-like)
    uint256 public totalDeposited;
    uint256 public accumulatedFees;
    bool private _locked;
    bool public paused;

    mapping(address => uint256) public shares;
    mapping(address => bool) public blacklisted;
    uint256 public totalShares;

    event Deposited(address indexed provider, uint256 amount, uint256 shares);
    event Withdrawn(address indexed provider, uint256 amount, uint256 shares);
    event FlashLoan(address indexed receiver, uint256 amount, uint256 fee);
    event FeeUpdated(uint256 newFee);
    event Blacklisted(address indexed target, bool status);

    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }
    modifier noReentrant() { require(!_locked, "Reentrant"); _locked = true; _; _locked = false; }
    modifier notPaused() { require(!paused, "Paused"); _; }

    constructor() { owner = msg.sender; }

    function deposit() external payable noReentrant notPaused {
        require(msg.value > 0, "Zero");
        uint256 sharesToMint;
        if (totalShares == 0 || totalDeposited == 0) {
            sharesToMint = msg.value;
        } else {
            sharesToMint = (msg.value * totalShares) / totalDeposited;
        }
        totalDeposited += msg.value;
        totalShares += sharesToMint;
        shares[msg.sender] += sharesToMint;
        emit Deposited(msg.sender, msg.value, sharesToMint);
    }

    function withdraw(uint256 shareAmount) external noReentrant {
        require(shares[msg.sender] >= shareAmount && shareAmount > 0, "Insufficient shares");
        uint256 assets = (shareAmount * totalDeposited) / totalShares;
        shares[msg.sender] -= shareAmount;
        totalShares -= shareAmount;
        totalDeposited -= assets;
        (bool ok,) = msg.sender.call{value: assets}("");
        require(ok, "Transfer failed");
        emit Withdrawn(msg.sender, assets, shareAmount);
    }

    function flashLoan(
        address receiver,
        uint256 amount,
        bytes calldata data
    ) external noReentrant notPaused returns (bool) {
        require(!blacklisted[receiver], "Blacklisted");
        require(amount > 0, "Zero amount");
        uint256 maxLoan = (totalDeposited * MAX_LOAN_PERCENT) / BPS;
        require(amount <= maxLoan, "Exceeds max loan");
        require(amount <= address(this).balance, "Insufficient liquidity");

        uint256 fee = flashFee(amount);
        uint256 balanceBefore = address(this).balance;

        (bool sent,) = receiver.call{value: amount}("");
        require(sent, "Loan transfer failed");

        bytes32 result = IFlashLoanReceiver(receiver).onFlashLoan(
            msg.sender, amount, fee, data
        );
        require(result == CALLBACK_SUCCESS, "Invalid callback");

        uint256 balanceAfter = address(this).balance;
        require(balanceAfter >= balanceBefore + fee, "Loan not repaid");

        uint256 actualFee = balanceAfter - balanceBefore;
        accumulatedFees += actualFee;
        totalDeposited += actualFee;

        emit FlashLoan(receiver, amount, actualFee);
        return true;
    }

    function flashFee(uint256 amount) public view returns (uint256) {
        return (amount * feeBps) / BPS;
    }

    function maxFlashLoan() external view returns (uint256) {
        return (totalDeposited * MAX_LOAN_PERCENT) / BPS;
    }

    function setFee(uint256 newFee) external onlyOwner {
        require(newFee <= MAX_FEE_BPS, "Fee too high");
        feeBps = newFee;
        emit FeeUpdated(newFee);
    }

    function setBlacklist(address target, bool status) external onlyOwner {
        blacklisted[target] = status;
        emit Blacklisted(target, status);
    }

    function pause() external onlyOwner { paused = true; }
    function unpause() external onlyOwner { paused = false; }

    function withdrawFees() external onlyOwner noReentrant {
        uint256 f = accumulatedFees;
        accumulatedFees = 0;
        totalDeposited -= f;
        (bool ok,) = owner.call{value: f}("");
        require(ok, "Failed");
    }

    function pricePerShare() external view returns (uint256) {
        if (totalShares == 0) return 1e18;
        return (totalDeposited * 1e18) / totalShares;
    }

    receive() external payable {}
}

contract MockFlashReceiver {
    bytes32 public constant CALLBACK_SUCCESS = keccak256("EIP3156FlashBorrower.onFlashLoan");
    address public pool;
    bool public shouldRepay;
    bool public shouldReturnWrong;

    constructor(address _pool) payable { pool = _pool; shouldRepay = true; }

    function setShouldRepay(bool v) external { shouldRepay = v; }
    function setShouldReturnWrong(bool v) external { shouldReturnWrong = v; }

    function onFlashLoan(address, uint256 amount, uint256 fee, bytes calldata)
        external returns (bytes32)
    {
        if (shouldRepay) {
            (bool ok,) = pool.call{value: amount + fee}("");
            require(ok, "Repay failed");
        }
        return shouldReturnWrong ? bytes32(0) : CALLBACK_SUCCESS;
    }

    receive() external payable {}
}