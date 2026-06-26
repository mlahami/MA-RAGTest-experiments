// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract StakingToken {
    string public name = "StakingToken";
    string public symbol = "STK";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    uint256 public constant REWARD_RATE = 100; // tokens per block
    uint256 public constant EARLY_WITHDRAWAL_PENALTY = 10; // 10%
    uint256 public constant MIN_STAKE_BLOCKS = 100;

    address public owner;
    bool private _locked;

    struct StakeInfo {
        uint256 amount;
        uint256 startBlock;
        uint256 rewardDebt;
    }

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => StakeInfo) public stakes;
    mapping(address => bool) public minters;

    uint256 public totalStaked;
    uint256 public accRewardPerShare;
    uint256 public lastRewardBlock;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Staked(address indexed user, uint256 amount);
    event Unstaked(address indexed user, uint256 amount, uint256 reward, uint256 penalty);

    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }
    modifier noReentrant() { require(!_locked, "Reentrant"); _locked = true; _; _locked = false; }

    constructor(uint256 _initialSupply) {
        owner = msg.sender;
        lastRewardBlock = block.number;
        _mint(msg.sender, _initialSupply * 10 ** decimals);
    }

    function _mint(address to, uint256 amount) internal {
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    function _updatePool() internal {
        if (block.number <= lastRewardBlock || totalStaked == 0) {
            lastRewardBlock = block.number;
            return;
        }
        uint256 blocks = block.number - lastRewardBlock;
        uint256 reward = blocks * REWARD_RATE * 1e18;
        accRewardPerShare += reward / totalStaked;
        lastRewardBlock = block.number;
    }

    function pendingRewards(address user) public view returns (uint256) {
        StakeInfo memory s = stakes[user];
        if (s.amount == 0) return 0;
        uint256 acc = accRewardPerShare;
        if (block.number > lastRewardBlock && totalStaked > 0) {
            uint256 blocks = block.number - lastRewardBlock;
            acc += (blocks * REWARD_RATE * 1e18) / totalStaked;
        }
        return (s.amount * acc / 1e18) - s.rewardDebt;
    }

    function stake(uint256 amount) external noReentrant {
        require(amount > 0, "Zero amount");
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        _updatePool();
        StakeInfo storage s = stakes[msg.sender];
        if (s.amount > 0) {
            uint256 pending = (s.amount * accRewardPerShare / 1e18) - s.rewardDebt;
            if (pending > 0) _mint(msg.sender, pending);
        }
        balanceOf[msg.sender] -= amount;
        totalStaked += amount;
        s.amount += amount;
        s.startBlock = block.number;
        s.rewardDebt = s.amount * accRewardPerShare / 1e18;
        emit Staked(msg.sender, amount);
    }

    function unstake(uint256 amount) external noReentrant {
        StakeInfo storage s = stakes[msg.sender];
        require(s.amount >= amount, "Insufficient stake");
        _updatePool();
        uint256 pending = (s.amount * accRewardPerShare / 1e18) - s.rewardDebt;
        uint256 penalty = 0;
        if (block.number < s.startBlock + MIN_STAKE_BLOCKS) {
            penalty = (amount * EARLY_WITHDRAWAL_PENALTY) / 100;
        }
        s.amount -= amount;
        totalStaked -= amount;
        s.rewardDebt = s.amount * accRewardPerShare / 1e18;
        uint256 net = amount - penalty;
        balanceOf[msg.sender] += net;
        if (penalty > 0) balanceOf[owner] += penalty;
        if (pending > 0) _mint(msg.sender, pending);
        emit Unstaked(msg.sender, amount, pending, penalty);
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(allowance[from][msg.sender] >= amount, "Allowance exceeded");
        require(balanceOf[from] >= amount, "Insufficient");
        allowance[from][msg.sender] -= amount;
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        emit Transfer(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external onlyOwner { _mint(to, amount); }
}