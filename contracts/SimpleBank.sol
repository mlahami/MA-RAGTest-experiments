// Benchmark candidate extracted from DeFiVulnLabs: DeFiVulnLabs/src/test/empty-loop.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract SimpleBank {
    struct Signature {
        bytes32 hash;
        uint8 v;
        bytes32 r;
        bytes32 s;
    }
    function verifySignatures(Signature calldata sig) public {
        require(
            msg.sender == ecrecover(sig.hash, sig.v, sig.r, sig.s),
            "Invalid signature"
        );
    }
    function withdraw(Signature[] calldata sigs) public {
        for (uint i = 0; i < sigs.length; i++) {
            Signature calldata signature = sigs[i];
            verifySignatures(signature);
        }
        payable(msg.sender).transfer(1 ether);
    }
    receive() external payable {}
}