// Benchmark candidate ported from smartbugs-curated: dataset/access_control/arbitrary_location_write_simple.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbArbitraryLocationWriteWallet {
    uint[] private bonusCodes;
    address private owner;

    constructor() {
        bonusCodes = new uint[](0);
        owner = msg.sender;
    }

    receive() external payable {
    }

    function PushBonusCode(uint c) public {
        bonusCodes.push(c);
    }

    function PopBonusCode() public {
        require(0 <= bonusCodes.length);
        assembly { sstore(bonusCodes.slot, sub(sload(bonusCodes.slot), 1)) }
    }

    function UpdateBonusCodeAt(uint idx, uint c) public {
        require(idx < bonusCodes.length);
        bonusCodes[idx] = c;
    }

    function Destroy() public {
        require(msg.sender == owner);
        selfdestruct(payable(msg.sender));
    }
}
