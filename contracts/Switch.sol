// Benchmark candidate extracted from Ethernaut: ethernaut/contracts/src/levels/Switch.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract Switch {
    bool public switchOn;
    bytes4 public offSelector = bytes4(keccak256("turnSwitchOff()"));
    modifier onlyThis() {
        require(msg.sender == address(this), "Only the contract can call this");
        _;
    }
    modifier onlyOff() {
        bytes32[1] memory selector;
        assembly {
            calldatacopy(selector, 68, 4)
        }
        require(selector[0] == offSelector, "Can only call the turnOffSwitch function");
        _;
    }
    function flipSwitch(bytes memory _data) public onlyOff {
        (bool success,) = address(this).call(_data);
        require(success, "call failed :(");
    }
    function turnSwitchOn() public onlyThis {
        switchOn = true;
    }
    function turnSwitchOff() public onlyThis {
        switchOn = false;
    }
}