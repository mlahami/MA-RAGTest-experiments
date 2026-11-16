// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0x19cf8481ea15427a98ba3cdd6d9e14690011ab10.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

interface SbDaoPolskaTokensTokenRecipient { function receiveApproval(address _from, uint256 _value, address _token, bytes calldata _extraData) external; }

interface SbDaoPolskaTokensMigrationAgent {
    function migrateFrom(address _from, uint256 _value) external;
}

abstract contract SbDaoPolskaTokensERC20 {
  uint public totalSupply;
  function balanceOf(address who) public view virtual returns (uint);
  function allowance(address owner, address spender) public view virtual returns (uint);

  function transfer(address to, uint value) public virtual returns (bool ok);
  function transferFrom(address from, address to, uint value) public virtual returns (bool ok);
  function approve(address spender, uint value) public virtual returns (bool ok);
  event Transfer(address indexed from, address indexed to, uint value);
  event Approval(address indexed owner, address indexed spender, uint value);
}

contract SbDaoPolskaTokensSafeMath {
  function safeMul(uint a, uint b) internal pure returns (uint) {
    uint c = a * b;
    assert(a == 0 || c / a == b);
    return c;
  }

  function safeDiv(uint a, uint b) internal pure returns (uint) {
    assert(b > 0);
    uint c = a / b;
    assert(a == b * c + a % b);
    return c;
  }

  function safeSub(uint a, uint b) internal pure returns (uint) {
    assert(b <= a);
    return a - b;
  }

  function safeAdd(uint a, uint b) internal pure returns (uint) {
    uint c = a + b;
    assert(c>=a && c>=b);
    return c;
  }

  function max64(uint64 a, uint64 b) internal pure returns (uint64) {
    return a >= b ? a : b;
  }

  function min64(uint64 a, uint64 b) internal pure returns (uint64) {
    return a < b ? a : b;
  }

  function max256(uint256 a, uint256 b) internal pure returns (uint256) {
    return a >= b ? a : b;
  }

  function min256(uint256 a, uint256 b) internal pure returns (uint256) {
    return a < b ? a : b;
  }
}

contract SbDaoPolskaTokensStandardToken is SbDaoPolskaTokensERC20, SbDaoPolskaTokensSafeMath {

  event Minted(address receiver, uint amount);

  mapping(address => uint) balances;
  mapping(address => uint) balancesRAW;
  mapping (address => mapping (address => uint)) allowed;

  function isToken() public pure returns (bool weAre) {
    return true;
  }

  function transfer(address _to, uint _value) public override returns (bool success) {
    balances[msg.sender] = safeSub(balances[msg.sender], _value);
    balances[_to] = safeAdd(balances[_to], _value);
    emit Transfer(msg.sender, _to, _value);
    return true;
  }

  function transferFrom(address _from, address _to, uint _value) public override returns (bool success) {
    uint _allowance = allowed[_from][msg.sender];

    balances[_to] = safeAdd(balances[_to], _value);
    balances[_from] = safeSub(balances[_from], _value);
    allowed[_from][msg.sender] = safeSub(_allowance, _value);
    emit Transfer(_from, _to, _value);
    return true;
  }

  function balanceOf(address _owner) public view override returns (uint balance) {
    return balances[_owner];
  }

  function approve(address _spender, uint _value) public override returns (bool success) {

    if ((_value != 0) && (allowed[msg.sender][_spender] != 0)) revert();

    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  function allowance(address _owner, address _spender) public view override returns (uint remaining) {
    return allowed[_owner][_spender];
  }

}

contract SbDaoPolskaTokens{

    string public name = "DAO POLSKA TOKEN version 1";
    string public symbol = "DPL";
    uint8 public constant decimals = 18;

    address public owner;
    address public migrationMaster;

    uint256 public otherchainstotalsupply =1.0 ether;
    uint256 public supplylimit      = 10000.0 ether;
   uint256 public  totalSupply      = 0.0 ether;
	address public Chain1 = address(0);
	address public Chain2 = address(0);
	address public Chain3 = address(0);
	address public Chain4 = address(0);

	address public migrationAgent;
    uint256 public totalMigrated;


    event Migrate(address indexed _from, address indexed _to, uint256 _value);
    event Refund(address indexed _from, uint256 _value);

	struct sendTokenAway{
		SbDaoPolskaTokensStandardToken coinContract;
		uint amount;
		address recipient;
	}
	mapping(uint => sendTokenAway) transfers;
	uint numTransfers=0;

  mapping (address => uint256) balances;
mapping (address => uint256) balancesRAW;
  mapping (address => mapping (address => uint256)) allowed;

	event UpdatedTokenInformation(string newName, string newSymbol);

    event Transfer(address indexed _from, address indexed _to, uint256 _value);
	event receivedEther(address indexed _from,uint256 _value);
  event Approval(address indexed _owner, address indexed _spender, uint256 _value);

    event Burn(address indexed from, uint256 value);
  bool public supplylimitset = false;
  bool public otherchainstotalset = false;

  constructor(address _migrationAgent, uint256 _fundingEndBlock) {
owner=msg.sender;
migrationMaster=msg.sender;
migrationAgent=_migrationAgent;
fundingEndBlock=_fundingEndBlock;
}

function  setSupply(uint256 supplyLOCKER) public {
    	   if (msg.sender != owner) {
      revert();
    }
		    	   if (supplylimitset != false) {
      revert();
    }
	supplylimitset = true;

	supplylimit = supplyLOCKER ** uint256(decimals);
  }
function setotherchainstotalsupply(uint256 supplyLOCKER) public {
    	   if (msg.sender != owner) {
      revert();
    }
	    	   if (supplylimitset != false) {
      revert();
    }

	otherchainstotalset = true;
	otherchainstotalsupply = supplyLOCKER ** uint256(decimals);

  }
    function approveAndCall(address _spender, uint256 _value, bytes memory _extraData)
        public
        returns (bool success) {
        SbDaoPolskaTokensTokenRecipient spender = SbDaoPolskaTokensTokenRecipient(_spender);
        if (approve(_spender, _value)) {
            spender.receiveApproval(msg.sender, _value, address(this), _extraData);
            return true;
        }
    }

    function burn(uint256 _value) public returns (bool success) {
        require(balances[msg.sender] >= _value);
        balances[msg.sender] -= _value;
        totalSupply -= _value;
        emit Burn(msg.sender, _value);
        return true;
    }

    function burnFrom(address _from, uint256 _value) public returns (bool success) {
        require(balances[_from] >= _value);
        require(_value <= allowed[_from][msg.sender]);
        balances[_from] -= _value;
        allowed[_from][msg.sender] -= _value;
        totalSupply -= _value;
        emit Burn(_from, _value);
        return true;
    }

  function transfer(address _to, uint256 _value) public returns (bool success) {
    if (balances[msg.sender] >= _value && balances[_to] + _value > balances[_to]) {
      balances[msg.sender] -= _value;
      balances[_to] += _value;
      emit Transfer(msg.sender, _to, _value);
      return true;
    } else { return false; }
  }

  function transferFrom(address _from, address _to, uint256 _value) public returns (bool success) {
    if (balances[_from] >= _value && allowed[_from][msg.sender] >= _value && balances[_to] + _value > balances[_to]) {
      balances[_to] += _value;
      balances[_from] -= _value;
      allowed[_from][msg.sender] -= _value;
      emit Transfer(_from, _to, _value);
      return true;
    } else { return false; }
  }

  function balanceOf(address _owner) public view returns (uint256 balance) {
    return balances[_owner];
  }

  function approve(address _spender, uint256 _value) public returns (bool success) {
    allowed[msg.sender][_spender] = _value;
    emit Approval(msg.sender, _spender, _value);
    return true;
  }

  function allowance(address _owner, address _spender) public view returns (uint256 remaining) {
    return allowed[_owner][_spender];
  }

	    receive() external payable {
		 if(funding){
        emit receivedEther(msg.sender, msg.value);
		balances[msg.sender]=balances[msg.sender]+msg.value;
		} else revert();

    }

  function setTokenInformation(string memory _name, string memory _symbol) public {

	   if (msg.sender != owner) {
      revert();
    }
	name = _name;
    symbol = _symbol;

    emit UpdatedTokenInformation(name, symbol);
  }

function setChainsAddresses(address chainAd, int chainnumber) public {

	   if (msg.sender != owner) {
      revert();
    }
	if(chainnumber==1){Chain1=chainAd;}
	if(chainnumber==2){Chain2=chainAd;}
	if(chainnumber==3){Chain3=chainAd;}
	if(chainnumber==4){Chain4=chainAd;}
  }

  function DAOPolskaTokenICOregulations() external pure returns(string memory wow) {
	return 'Regulations of preICO and ICO are present at website  DAO Polska Token.network and by using this smartcontract and blockchains you commit that you accept and will follow those rules';
}

	function sendTokenAw(address StandardTokenAddress, address receiver, uint amount) public {
		if (msg.sender != owner) {
		revert();
		}
		sendTokenAway storage t = transfers[numTransfers];
		t.coinContract = SbDaoPolskaTokensStandardToken(StandardTokenAddress);
		t.amount = amount;
		t.recipient = receiver;
		t.coinContract.transfer(receiver, amount);
		numTransfers++;
	}

uint public tokenCreationRate=1000;
uint public bonusCreationRate=1000;
uint public CreationRate=1761;
   uint256 public constant oneweek = 36000;
uint256 public fundingEndBlock;
bool public funding = true;
bool public refundstate = false;
bool public migratestate= false;
        function createDaoPOLSKAtokens(address holder) public payable {

        if (!funding) revert();

        if (msg.value == 0) revert();
        unchecked {
        if (msg.value > (supplylimit - totalSupply) / CreationRate)
          revert();
        }

	 uint256 numTokensRAW = msg.value;

        uint256 numTokens = msg.value * CreationRate;
        totalSupply += numTokens;

        balances[holder] += numTokens;
        balancesRAW[holder] += numTokensRAW;
        emit Transfer(address(0), holder, numTokens);

        uint256 percentOfTotal = 12;
        uint256 additionalTokens = 	numTokens * percentOfTotal / (100);

        totalSupply += additionalTokens;

        balances[migrationMaster] += additionalTokens;
        emit Transfer(address(0), migrationMaster, additionalTokens);

	}
	function setBonusCreationRate(uint newRate) public {
	if(msg.sender == owner) {
	bonusCreationRate=newRate;
	CreationRate=tokenCreationRate+bonusCreationRate;
	}
	}

    function FundsTransfer() external {
	if(funding==true) revert();
		 	if (!payable(owner).send(address(this).balance)) revert();
    }

    function PartialFundsTransfer(uint SubX) external {
	      if (msg.sender != owner) revert();
        unchecked { payable(owner).send(address(this).balance - SubX); }
	}
	function turnrefund() external {
	      if (msg.sender != owner) revert();
	refundstate=!refundstate;
        }

			function fundingState() external {
	      if (msg.sender != owner) revert();
	funding=!funding;
        }
    function turnmigrate() external {
	      if (msg.sender != migrationMaster) revert();
	migratestate=!migratestate;
}

function finalize() external {
        if (block.number <= fundingEndBlock+8*oneweek) revert();
        funding = false;
		refundstate=!refundstate;
        if (msg.sender==owner)
		payable(owner).send(address(this).balance);
    }
    function migrate(uint256 _value) external {
        if (migratestate) revert();

        if (_value == 0) revert();
        if (_value > balances[msg.sender]) revert();

        balances[msg.sender] -= _value;
        totalSupply -= _value;
        totalMigrated += _value;
        SbDaoPolskaTokensMigrationAgent(migrationAgent).migrateFrom(msg.sender, _value);
        emit Migrate(msg.sender, migrationAgent, _value);
    }

function refundTRA() external {
        if (funding) revert();
        if (!refundstate) revert();

        uint256 DAOPLTokenValue = balances[msg.sender];
        uint256 ETHValue = balancesRAW[msg.sender];
        if (ETHValue == 0) revert();
        balancesRAW[msg.sender] = 0;
        totalSupply -= DAOPLTokenValue;

        emit Refund(msg.sender, ETHValue);
        payable(msg.sender).transfer(ETHValue);
}

function preICOregulations() external pure returns(string memory wow) {
	return 'Regulations of preICO are present at website  daopolska.pl and by using this smartcontract you commit that you accept and will follow those rules';
}

}
