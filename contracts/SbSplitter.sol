// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0xb0510d68f210b7db66e8c7c814f22680f2b8d1d6.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbSplitter{

	address public owner;
	address[] public puppets;
	mapping (uint256 => address) public extra;
	address private _addy;
	uint256 private _share;
	uint256 private _count;
	address public puppetTarget;
	address public puppetMaster;

	constructor(address _puppetTarget, address _puppetMaster) payable {
		owner = msg.sender;
		puppetTarget = _puppetTarget;
		puppetMaster = _puppetMaster;
		newPuppet();
		newPuppet();
		newPuppet();
		newPuppet();
		extra[0] = puppets[0];
        extra[1] = puppets[1];
        extra[2] = puppets[2];
        extra[3] = puppets[3];
	}

	function withdraw() public{
		require(msg.sender == owner);
		payable(owner).transfer(address(this).balance);
	}

	function getPuppetCount() public view returns(uint256 puppetCount){
    	return puppets.length;
  	}

	function newPuppet() public returns(address newPuppetAddress){
	    require(msg.sender == owner);
    	SbSplitterPuppet p = new SbSplitterPuppet(puppetTarget, puppetMaster);
    	puppets.push(address(p));
    	return address(p);
  		}

    function setExtra(uint256 _id, address _newExtra) public {
        require(_newExtra != address(0));
        extra[_id] = _newExtra;
    }

    function fundPuppets() public payable {
        require(msg.sender == owner);
    	_share = SbSplitterSafeMath.div(msg.value, 4);
        extra[0].call{value: _share, gas: 800000}("");
        extra[1].call{value: _share, gas: 800000}("");
        extra[2].call{value: _share, gas: 800000}("");
        extra[3].call{value: _share, gas: 800000}("");
        }

receive() external payable{
	}
}

contract SbSplitterPuppet {

    mapping (uint256 => address) public target;
    mapping (uint256 => address) public master;

	constructor(address _target, address _master) payable {
		target[0] = _target;
        master[0] = _master;
	}

	receive() external payable{
	    if(msg.sender != target[0]){
			target[0].call{value: msg.value, gas: 600000}("");
		}
    }

	function withdraw() public{
		require(msg.sender == master[0]);
		payable(master[0]).transfer(address(this).balance);
	}
}

library SbSplitterSafeMath {

  function mul(uint256 a, uint256 b) internal pure returns (uint256 c) {
    if (a == 0) {
      return 0;
    }
    c = a * b;
    assert(c / a == b);
    return c;
  }

  function div(uint256 a, uint256 b) internal pure returns (uint256) {
    return a / b;
  }

  function sub(uint256 a, uint256 b) internal pure returns (uint256) {
    assert(b <= a);
    return a - b;
  }

  function add(uint256 a, uint256 b) internal pure returns (uint256 c) {
    c = a + b;
    assert(c >= a);
    return c;
  }
}
