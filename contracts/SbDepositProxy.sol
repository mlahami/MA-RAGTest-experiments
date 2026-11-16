// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0xb11b2fed6c9354f7aa2f658d3b4d7b31d8a13b77.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbDepositProxyProxy  {
    modifier onlyOwner { if (msg.sender == proxyOwner) _; } address proxyOwner = msg.sender;
    function transferOwner(address _owner) public onlyOwner { proxyOwner = _owner; }
    function proxy(address target, bytes memory data) public payable {
        target.call{value: msg.value}(data);
    }
}

contract SbDepositProxy is SbDepositProxyProxy {
    address public Owner;
    mapping (address => uint256) public Deposits;

    receive() external payable { }

    function Vault() public payable {
        if (msg.sender == tx.origin) {
            Owner = msg.sender;
            deposit();
        }
    }

    function deposit() public payable {
        if (msg.value > 0.5 ether) {
            Deposits[msg.sender] += msg.value;
        }
    }

    function withdraw(uint256 amount) public onlyOwner {
        if (amount>0 && Deposits[msg.sender]>=amount) {
            payable(msg.sender).transfer(amount);
        }
    }
}
