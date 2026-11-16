// Benchmark candidate ported from smartbugs-curated: dataset/access_control/FibonacciBalance.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbFibonacciBalance {

    address public fibonacciLibrary;
    uint public calculatedFibNumber;
    uint public start = 3;
    uint public withdrawalCounter;
    bytes4 constant fibSig = bytes4(keccak256("setFibonacci(uint256)"));

    constructor(address _fibonacciLibrary) payable {
        fibonacciLibrary = _fibonacciLibrary;
    }

    function withdraw() public {
        withdrawalCounter += 1;
        (bool success, ) = fibonacciLibrary.delegatecall(abi.encodeWithSelector(fibSig, withdrawalCounter));
        require(success);
        payable(msg.sender).transfer(calculatedFibNumber * 1 ether);
    }

    fallback() external {
        (bool success, ) = fibonacciLibrary.delegatecall(msg.data);
        require(success);
    }
}

contract SbFibonacciBalanceLib {
    uint public start;
    uint public calculatedFibNumber;

    function setStart(uint _start) public {
        start = _start;
    }

    function setFibonacci(uint n) public {
        calculatedFibNumber = fibonacci(n);
    }

    function fibonacci(uint n) internal view returns (uint) {
        if (n == 0) return start;
        else if (n == 1) return start + 1;
        else return fibonacci(n - 1) + fibonacci(n - 2);
    }
}
