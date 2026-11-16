// Benchmark candidate ported from smartbugs-curated: dataset/arithmetic/BECToken.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

library SbBecTokenSafeMath {
  function mul(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a * b;
    require(a == 0 || c / a == b);
    return c;
  }

  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a / b;
    return c;
  }

  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    require(b <= a);
    return a - b;
  }

  function add(uint256 a, uint256 b) internal pure returns (uint256) {
    uint256 c = a + b;
    require(c >= a);
    return c;
  }
}

abstract contract SbBecTokenERC20Basic {
  uint256 public totalSupply;
  function balanceOf(address who) public view virtual returns (uint256);
  function transfer(address to, uint256 value) public virtual returns (bool);
  event Transfer(address indexed from, address indexed to, uint256 value);
}

contract SbBecTokenBasicToken is SbBecTokenERC20Basic {
  using SbBecTokenSafeMath for uint256;

  mapping(address => uint256) balances;

  function transfer(address _to, uint256 _value) public virtual override returns (bool) {
    require(_to != address(0));
    require(_value > 0 && _value <= balances[msg.sender]);

    balances[msg.sender] = balances[msg.sender].sub(_value);
    balances[_to] = balances[_to].add(_value);
    emit Transfer(msg.sender, _to, _value);
    return true;
  }

  function balanceOf(address _owner) public view virtual override returns (uint256 balance) {
    return balances[_owner];
  }
}

abstract contract SbBecTokenERC20 is SbBecTokenERC20Basic {
  function allowance(address owner, address spender) public view virtual returns (uint256);
  function transferFrom(address from, address to, uint256 value) public virtual returns (bool);
  function approve(address spender, uint256 value) public virtual returns (bool);
  event Approval(address indexed owner, address indexed spender, uint256 value);
}

contract SbBecTokenStandardToken is SbBecTokenERC20, SbBecTokenBasicToken {
  using SbBecTokenSafeMath for uint256;

  mapping (address => mapping (address => uint256)) internal allowed;

  function transferFrom(address _from, address _to, uint256 _value) public virtual override returns (bool) {
    require(_to != address(0));
    require(_value > 0 && _value <= balances[_from]);
    require(_value <= allowed[_from][msg.sender]);

    balances[_from] = balances[_from].sub(_value);
    balances[_to] = balances[_to].add(_value);
    allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  function approve(address _spender, uint256 _value) public virtual override returns (bool) {
    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  function allowance(address _owner, address _spender) public view override returns (uint256 remaining) {
    return allowed[_owner][_spender];
  }
}

contract SbBecTokenOwnable {
  address public owner;

  event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

  constructor() {
    owner = msg.sender;
  }

  modifier onlyOwner() {
    require(msg.sender == owner);
    _;
  }

  function transferOwnership(address newOwner) onlyOwner public {
    require(newOwner != address(0));
    emit OwnershipTransferred(owner, newOwner);
    owner = newOwner;
  }

}

contract SbBecTokenPausable is SbBecTokenOwnable {
  event Pause();
  event Unpause();

  bool public paused = false;

  modifier whenNotPaused() {
    require(!paused);
    _;
  }

  modifier whenPaused() {
    require(paused);
    _;
  }

  function pause() onlyOwner whenNotPaused public {
    paused = true;
    emit Pause();
  }

  function unpause() onlyOwner whenPaused public {
    paused = false;
    emit Unpause();
  }
}

contract SbBecTokenPausableToken is SbBecTokenStandardToken, SbBecTokenPausable {
  using SbBecTokenSafeMath for uint256;

  function transfer(address _to, uint256 _value) public override(SbBecTokenERC20Basic, SbBecTokenBasicToken) whenNotPaused returns (bool) {
    return super.transfer(_to, _value);
  }

  function transferFrom(address _from, address _to, uint256 _value) public override whenNotPaused returns (bool) {
    return super.transferFrom(_from, _to, _value);
  }

  function approve(address _spender, uint256 _value) public override whenNotPaused returns (bool) {
    return super.approve(_spender, _value);
  }

  function batchTransfer(address[] memory _receivers, uint256 _value) public whenNotPaused returns (bool) {
    uint cnt = _receivers.length;
    uint256 amount;
    unchecked { amount = uint256(cnt) * _value; }
    require(cnt > 0 && cnt <= 20);
    require(_value > 0 && balances[msg.sender] >= amount);

    balances[msg.sender] = balances[msg.sender].sub(amount);
    for (uint i = 0; i < cnt; i++) {
        balances[_receivers[i]] = balances[_receivers[i]].add(_value);
        emit Transfer(msg.sender, _receivers[i], _value);
    }
    return true;
  }
}

contract SbBecToken is SbBecTokenPausableToken {
    string public name = "BeautyChain";
    string public symbol = "BEC";
    string public version = "1.0.0";
    uint8 public decimals = 18;

    constructor() {
      totalSupply = 7000000000 * (10**(uint256(decimals)));
      balances[msg.sender] = totalSupply;
    }

    fallback() external {
        revert();
    }
}
