// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0x9d06cbafa865037a01d322d3f4222fa3e04e5488.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbDelta {

	address public c;
	address public owner;
	address public owner2;
	uint public active = 1;

	uint public token_price = 10**18*1/1000;

	constructor(address _c, address _owner2) {
		c = _c;
		owner = msg.sender;
		owner2 = _owner2;
	}

	receive() external payable {
	    tokens_buy();
	}

    function tokens_buy() public payable returns (bool) {

        require(active > 0);
        require(msg.value >= token_price);

        uint tokens_buy = msg.value*10**18/token_price;

        require(tokens_buy > 0);

        (bool ok, ) = c.call(abi.encodeWithSignature("transferFrom(address,address,uint256)", owner, msg.sender, tokens_buy));
        if(!ok){
        	return false;
        }

        uint sum2 = msg.value * 3 / 10;
        payable(owner2).send(sum2);

        return true;
      }

      function withdraw(uint256 _amount) public onlyOwner returns (bool result) {
          uint256 balance;
          balance = address(this).balance;
          if(_amount > 0) balance = _amount;
          payable(owner).send(balance);
          return true;
      }

      function change_token_price(uint256 _token_price) public onlyOwner returns (bool result) {
        token_price = _token_price;
        return true;
      }

      function change_active(uint256 _active) public onlyOwner returns (bool result) {
        active = _active;
        return true;
      }

    	modifier onlyOwner() {
        if (msg.sender != owner) {
            revert();
        }
        _;
    }

}
