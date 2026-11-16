// Benchmark candidate ported from smartbugs-curated: dataset/time_manipulation/governmental_survey.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbGovernmental {
  address public owner;
  address public lastInvestor;
  uint public jackpot = 1 ether;
  uint public lastInvestmentTimestamp;
  uint public ONE_MINUTE = 1 minutes;

  constructor() payable {
    owner = msg.sender;
    if (msg.value<1 ether) revert();
  }

  function invest() public payable {
    if (msg.value<jackpot/2) revert();
    lastInvestor = msg.sender;
    jackpot += msg.value/2;
    lastInvestmentTimestamp = block.timestamp;
  }

  function resetInvestment() public {
    if (block.timestamp < lastInvestmentTimestamp+ONE_MINUTE)
      revert();

    payable(lastInvestor).send(jackpot);
    unchecked { payable(owner).send(address(this).balance-1 ether); }

    lastInvestor = address(0);
    jackpot = 1 ether;
    lastInvestmentTimestamp = 0;
  }
}
