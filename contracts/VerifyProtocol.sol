// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * Verify Protocol
 * On-chain identity registry for autonomous agents.
 *
 * AI agents are moving money. $500K was drained last week through a
 * compromised LLM router. Nobody verified who the agent was. Nobody
 * checked if the agent was authorized. Nobody knew until it was gone.
 *
 * This is the problem Verify exists to solve.
 *
 * Any wallet can register as a verified agent by staking VRFY tokens.
 * Staked agents receive an on-chain credential — a trust score that
 * increases with time staked and tokens committed. Agents with higher
 * scores are more trustworthy because they have more to lose.
 *
 * Other contracts can call isVerified() to check if an agent has
 * active credentials before processing its transactions. Simple
 * boolean check. One line of code to integrate.
 *
 * Unstake anytime. No lock. But your trust score resets to zero.
 * Building trust takes time. Losing it takes one transaction.
 *
 * TOKEN: 25,000,000 VRFY — fixed supply, no mint function.
 * TAX: 0% on all transfers.
 * OWNER: Can only renounce. No other privileges.
 *
 * Built for the agent economy. Read the code.
 */
contract VerifyProtocol {

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Burned(address indexed from, uint256 amount);
    event OwnershipRenounced(address indexed prev);
    event AgentRegistered(address indexed agent, uint256 stake, uint256 timestamp);
    event AgentRevoked(address indexed agent, uint256 returned);
    event TrustUpdated(address indexed agent, uint256 newScore);

    string  public constant name     = "Verify Protocol";
    string  public constant symbol   = "VRFY";
    uint8   public constant decimals = 18;
    uint256 public constant CAP      = 25_000_000 * 1e18;
    uint256 public constant MIN_STAKE = 500 * 1e18;

    address public owner;
    uint256 public totalBurned;
    uint256 public registeredAgents;
    uint256 public totalStaked;

    mapping(address => uint256) private _bal;
    mapping(address => mapping(address => uint256)) private _allowance;

    struct Agent {
        uint256 stake;
        uint256 since;
        bool    active;
    }

    mapping(address => Agent) public agents;

    constructor() {
        owner = msg.sender;
        _bal[msg.sender] = CAP;
        emit Transfer(address(0), msg.sender, CAP);
    }

    // ── ERC-20 ────────────────────────────────────────────────────────────────

    function totalSupply() external view returns (uint256) { return CAP - totalBurned; }
    function balanceOf(address a) external view returns (uint256) { return _bal[a]; }
    function allowance(address o, address s) external view returns (uint256) { return _allowance[o][s]; }

    function transfer(address to, uint256 v) external returns (bool) {
        _xfer(msg.sender, to, v);
        return true;
    }

    function approve(address s, uint256 v) external returns (bool) {
        require(s != address(0));
        _allowance[msg.sender][s] = v;
        emit Approval(msg.sender, s, v);
        return true;
    }

    function transferFrom(address f, address t, uint256 v) external returns (bool) {
        uint256 a = _allowance[f][msg.sender];
        if (a != type(uint256).max) {
            require(a >= v, "VRFY: allowance");
            unchecked { _allowance[f][msg.sender] = a - v; }
        }
        _xfer(f, t, v);
        return true;
    }

    function burn(uint256 v) external {
        require(_bal[msg.sender] >= v, "VRFY: balance");
        unchecked { _bal[msg.sender] -= v; totalBurned += v; }
        emit Transfer(msg.sender, address(0), v);
        emit Burned(msg.sender, v);
    }

    // ── Agent Registry ────────────────────────────────────────────────────────

    /// @notice Register as a verified agent by staking VRFY tokens.
    function register(uint256 amount) external {
        require(amount >= MIN_STAKE, "VRFY: min 500");
        require(!agents[msg.sender].active, "VRFY: already registered");
        require(_bal[msg.sender] >= amount, "VRFY: balance");

        unchecked { _bal[msg.sender] -= amount; }
        _bal[address(this)] += amount;
        totalStaked += amount;
        registeredAgents++;

        agents[msg.sender] = Agent({
            stake: amount,
            since: block.timestamp,
            active: true
        });

        emit Transfer(msg.sender, address(this), amount);
        emit AgentRegistered(msg.sender, amount, block.timestamp);
    }

    /// @notice Increase your stake to boost trust score.
    function boost(uint256 amount) external {
        require(agents[msg.sender].active, "VRFY: not registered");
        require(_bal[msg.sender] >= amount, "VRFY: balance");

        unchecked { _bal[msg.sender] -= amount; }
        _bal[address(this)] += amount;
        agents[msg.sender].stake += amount;
        totalStaked += amount;

        emit Transfer(msg.sender, address(this), amount);
        emit TrustUpdated(msg.sender, trustScore(msg.sender));
    }

    /// @notice Revoke registration and withdraw stake. Trust score resets.
    function revoke() external {
        Agent storage a = agents[msg.sender];
        require(a.active, "VRFY: not registered");

        uint256 amount = a.stake;
        a.stake = 0;
        a.active = false;
        a.since = 0;
        registeredAgents--;
        totalStaked -= amount;

        _bal[address(this)] -= amount;
        _bal[msg.sender] += amount;

        emit Transfer(address(this), msg.sender, amount);
        emit AgentRevoked(msg.sender, amount);
    }

    // ── Reads ─────────────────────────────────────────────────────────────────

    /// @notice Check if an address has active verified credentials.
    function isVerified(address who) external view returns (bool) {
        return agents[who].active;
    }

    /// @notice Trust score: stake amount * days registered (max 100).
    function trustScore(address who) public view returns (uint256) {
        Agent storage a = agents[who];
        if (!a.active) return 0;
        uint256 days_ = (block.timestamp - a.since) / 1 days;
        if (days_ == 0) days_ = 1;
        uint256 stakeUnits = a.stake / (100 * 1e18);
        uint256 score = stakeUnits * days_;
        return score > 100 ? 100 : score;
    }

    /// @notice Full agent credential check.
    function credential(address who) external view returns (
        bool active,
        uint256 stake,
        uint256 since,
        uint256 score
    ) {
        Agent storage a = agents[who];
        return (a.active, a.stake, a.since, trustScore(who));
    }

    /// @notice Protocol stats.
    function protocol() external view returns (
        uint256 supply,
        uint256 burned,
        uint256 agents_,
        uint256 staked
    ) {
        return (CAP - totalBurned, totalBurned, registeredAgents, totalStaked);
    }

    // ── Ownership ─────────────────────────────────────────────────────────────

    function renounceOwnership() external {
        require(msg.sender == owner);
        emit OwnershipRenounced(owner);
        owner = address(0);
    }

    // ── Internal ──────────────────────────────────────────────────────────────

    function _xfer(address f, address t, uint256 v) internal {
        require(f != address(0) && t != address(0));
        require(_bal[f] >= v, "VRFY: balance");
        unchecked { _bal[f] -= v; _bal[t] += v; }
        emit Transfer(f, t, v);
    }
}
