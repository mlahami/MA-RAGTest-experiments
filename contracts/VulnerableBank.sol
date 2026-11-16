// Benchmark candidate extracted from DeFiVulnLabs: DeFiVulnLabs/src/test/Incorrect_sanity_checks.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract VulnerableBank {
    struct Locker {
        bool hasLockedTokens;
        uint256 amount;
        uint256 lockTime;
        address tokenAddress;
    }
    mapping(address => mapping(uint256 => Locker)) private _unlockToken;
    uint256 private _nextLockerId = 1;
    function createLocker(
        address tokenAddress,
        uint256 amount,
        uint256 lockTime
    ) public {
        require(amount > 0, "Amount must be greater than 0");
        require(lockTime > block.timestamp, "Lock time must be in the future");
        require(
            IERC20(tokenAddress).balanceOf(msg.sender) >= amount,
            "Insufficient token balance"
        );
        IERC20(tokenAddress).transferFrom(msg.sender, address(this), amount);
        Locker storage locker = _unlockToken[msg.sender][_nextLockerId];
        locker.hasLockedTokens = true;
        locker.amount = amount;
        locker.lockTime = lockTime;
        locker.tokenAddress = tokenAddress;
        _nextLockerId++;
    }
    function unlockToken(uint256 lockerId) public {
        Locker storage locker = _unlockToken[msg.sender][lockerId];
        uint256 amount = locker.amount;
        require(locker.hasLockedTokens, "No locked tokens");
        if (block.timestamp > locker.lockTime) {
            locker.amount = 0;
        }
        IERC20(locker.tokenAddress).transfer(msg.sender, amount);
    }
}
contract VulnerableBankMockToken is ERC20 {
    constructor(string memory name_, string memory symbol_) ERC20(name_, symbol_) {}
    function mint(address to, uint256 amount) external { _mint(to, amount); }
}
