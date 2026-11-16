// Benchmark candidate extracted from SolidityByExample/app: solidity-by-example.github.io/src/pages/app/deploy-any-contract/Proxy.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract SbeProxy {
    event Deploy(address);
    receive() external payable {}
    function deploy(bytes memory _code)
        external
        payable
        returns (address addr)
    {
        assembly {
            addr := create(callvalue(), add(_code, 0x20), mload(_code))
        }
        require(addr != address(0), "deploy failed");
        emit Deploy(addr);
    }
    function execute(address _target, bytes memory _data) external payable {
        (bool success,) = _target.call{value: msg.value}(_data);
        require(success, "failed");
    }
}