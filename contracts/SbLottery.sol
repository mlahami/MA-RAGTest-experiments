// Benchmark candidate ported from smartbugs-curated: dataset/bad_randomness/lottery.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

 contract SbLottery {
     event GetBet(uint betAmount, uint blockNumber, bool won);

     struct Bet {
         uint betAmount;
         uint blockNumber;
         bool won;
     }

     address private organizer;
     Bet[] private bets;

     constructor() {
         organizer = msg.sender;
     }

     fallback() external {
         revert();
     }

     function makeBet() public payable {
         bool won = (block.number % 2) == 0;

         bets.push(Bet(msg.value, block.number, won));

         if(won) {
             if(!payable(msg.sender).send(msg.value)) {
                 revert();
             }
         }
     }

     function getBets() public {
         if(msg.sender != organizer) { revert(); }

         for (uint i = 0; i < bets.length; i++) {
             emit GetBet(bets[i].betAmount, bets[i].blockNumber, bets[i].won);
         }
     }

     function destroy() public {
         if(msg.sender != organizer) { revert(); }

         selfdestruct(payable(organizer));
     }
 }
