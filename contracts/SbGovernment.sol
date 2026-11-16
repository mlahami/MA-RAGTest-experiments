// Benchmark candidate ported from smartbugs-curated: dataset/denial_of_service/list_dos.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbGovernment {

     uint32 public lastCreditorPayedOut;
     uint public lastTimeOfNewCredit;
     uint public profitFromCrash;
     address[] public creditorAddresses;
     uint[] public creditorAmounts;
     address public corruptElite;
     mapping (address => uint) buddies;
     uint constant TWELVE_HOURS = 43200;
     uint8 public round;

     constructor() payable {
         profitFromCrash = msg.value;
         corruptElite = msg.sender;
         lastTimeOfNewCredit = block.timestamp;
     }

     function lendGovernmentMoney(address buddy) public payable returns (bool) {
         uint amount = msg.value;
         if (lastTimeOfNewCredit + TWELVE_HOURS < block.timestamp) {
             payable(msg.sender).send(amount);
             payable(creditorAddresses[creditorAddresses.length - 1]).send(profitFromCrash);
             payable(corruptElite).send(address(this).balance);
             lastCreditorPayedOut = 0;
             lastTimeOfNewCredit = block.timestamp;
             profitFromCrash = 0;
             creditorAddresses = new address[](0);
             creditorAmounts = new uint[](0);
             unchecked { round += 1; }
             return false;
         }
         else {
             if (amount >= 10 ** 18) {
                 lastTimeOfNewCredit = block.timestamp;
                 creditorAddresses.push(msg.sender);
                 creditorAmounts.push(amount * 110 / 100);
                 payable(corruptElite).send(amount * 5/100);
                 if (profitFromCrash < 10000 * 10**18) {
                     profitFromCrash += amount * 5/100;
                 }
                 if(buddies[buddy] >= amount) {
                     payable(buddy).send(amount * 5/100);
                 }
                 buddies[msg.sender] += amount * 110 / 100;
                 unchecked {
                     if (creditorAmounts[lastCreditorPayedOut] <= address(this).balance - profitFromCrash) {
                         payable(creditorAddresses[lastCreditorPayedOut]).send(creditorAmounts[lastCreditorPayedOut]);
                         buddies[creditorAddresses[lastCreditorPayedOut]] -= creditorAmounts[lastCreditorPayedOut];
                         lastCreditorPayedOut += 1;
                     }
                 }
                 return true;
             }
             else {
                 payable(msg.sender).send(amount);
                 return false;
             }
         }
     }

     fallback() external payable {
         lendGovernmentMoney(address(0));
     }

     function totalDebt() public view returns (uint debt) {
         for(uint i=lastCreditorPayedOut; i<creditorAmounts.length; i++){
             debt += creditorAmounts[i];
         }
     }

     function totalPayedOut() public view returns (uint payout) {
         for(uint i=0; i<lastCreditorPayedOut; i++){
             payout += creditorAmounts[i];
         }
     }

     function investInTheSystem() public payable {
         profitFromCrash += msg.value;
     }

     function inheritToNextGeneration(address nextGeneration) public {
         if (msg.sender == corruptElite) {
             corruptElite = nextGeneration;
         }
     }

     function getCreditorAddresses() public view returns (address[] memory) {
         return creditorAddresses;
     }

     function getCreditorAmounts() public view returns (uint[] memory) {
         return creditorAmounts;
     }
 }
