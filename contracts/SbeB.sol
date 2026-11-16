// Benchmark candidate extracted from SolidityByExample/hacks: solidity-by-example.github.io/src/pages/hacks/63-64-gas-rule/Gas.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract SbeB {
    event Log(uint256 gas);
    mapping(address => bool) public authorized;
    constructor() {
        authorized[msg.sender] = true;
    }
    receive() external payable {}
    function setAuth(address addr, bool auth) external {
        require(authorized[msg.sender], "not authorized");
        authorized[addr] = auth;
    }
    function g(address receiver, uint256 gasStart) external {
        require(authorized[msg.sender], "not authorized");
        uint256 gasNow = gasleft();
        uint256 gasUsed = gasStart - gasNow;
        (bool ok,) = receiver.call{value: gasUsed}("");
        require(ok, "send failed");
        emit Log(gasUsed);
    }
}