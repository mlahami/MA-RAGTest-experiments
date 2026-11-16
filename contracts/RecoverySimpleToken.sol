// Benchmark candidate extracted from Ethernaut: ethernaut/contracts/src/levels/RecoverySimpleToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract RecoverySimpleToken {
    string public name;
    mapping(address => uint256) public balances;
    constructor(string memory _name, address _creator, uint256 _initialSupply) {
        name = _name;
        balances[_creator] = _initialSupply;
    }
    receive() external payable {
        balances[msg.sender] += msg.value * 10;
    }
    function transfer(address _to, uint256 _amount) public {
        require(balances[msg.sender] >= _amount);
        balances[msg.sender] = balances[msg.sender] - _amount;
        balances[_to] = _amount;
    }
    function destroy(address payable to) public {
        selfdestruct(to);
    }
}