// Benchmark candidate extracted from Ethernaut: ethernaut/contracts/src/levels/Denial.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;



contract Denial {
    address public partner;
    address public constant owner = address(0xA9E);
    uint256 timeLastWithdrawn;
    mapping(address => uint256) withdrawPartnerBalances;
    function setWithdrawPartner(address _partner) public {
        partner = _partner;
    }
    function withdraw() public {
        uint256 amountToSend = address(this).balance / 100;
        partner.call{value: amountToSend}("");
        payable(owner).transfer(amountToSend);
        timeLastWithdrawn = block.timestamp;
        withdrawPartnerBalances[partner] += amountToSend;
    }
    receive() external payable {}
    function contractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}