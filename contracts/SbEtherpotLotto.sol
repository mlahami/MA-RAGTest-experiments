// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/etherpot_lotto.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

 contract SbEtherpotLotto {

     uint constant public blocksPerRound = 6800;

     uint constant public ticketPrice = 100000000000000000;

     uint constant public blockReward = 5000000000000000000;

     function getBlocksPerRound() public pure returns(uint){ return blocksPerRound; }
     function getTicketPrice() public pure returns(uint){ return ticketPrice; }

     struct Round {
         address[] buyers;
         uint pot;
         uint ticketsCount;
         mapping(uint=>bool) isCashed;
         mapping(address=>uint) ticketsCountByBuyer;
     }
     mapping(uint => Round) rounds;

     function getRoundIndex() public view returns (uint){

         return block.number/blocksPerRound;
     }

     function getIsCashed(uint roundIndex,uint subpotIndex) public view returns (bool){

         return rounds[roundIndex].isCashed[subpotIndex];
     }


     function calculateWinner(uint roundIndex, uint subpotIndex) public view returns(address){

         uint decisionBlockNumber = getDecisionBlockNumber(roundIndex,subpotIndex);

         if(decisionBlockNumber>block.number)
             return address(0);

         uint decisionBlockHash = getHashOfBlock(decisionBlockNumber);
         uint winningTicketIndex = decisionBlockHash%rounds[roundIndex].ticketsCount;

         uint256 ticketIndex = uint256(0);

         for(uint8 buyerIndex = 0; buyerIndex<rounds[roundIndex].buyers.length; buyerIndex++){
             address buyer = rounds[roundIndex].buyers[buyerIndex];
             ticketIndex+=rounds[roundIndex].ticketsCountByBuyer[buyer];

             if(ticketIndex>winningTicketIndex){
                 return buyer;
             }
         }
         return address(0);
     }

     function getDecisionBlockNumber(uint roundIndex,uint subpotIndex) public pure returns (uint){
         return ((roundIndex+1)*blocksPerRound)+subpotIndex;
     }

     function getSubpotsCount(uint roundIndex) public view returns(uint){
         uint subpotsCount = rounds[roundIndex].pot/blockReward;

         if(rounds[roundIndex].pot%blockReward>0)
             subpotsCount++;

         return subpotsCount;
     }

     function getSubpot(uint roundIndex) public view returns(uint){
         return rounds[roundIndex].pot/getSubpotsCount(roundIndex);
     }

     function cash(uint roundIndex, uint subpotIndex) public {

         uint subpotsCount = getSubpotsCount(roundIndex);

         if(subpotIndex>=subpotsCount)
             return;

         uint decisionBlockNumber = getDecisionBlockNumber(roundIndex,subpotIndex);

         if(decisionBlockNumber>block.number)
             return;

         if(rounds[roundIndex].isCashed[subpotIndex])
             return;

         address winner = calculateWinner(roundIndex,subpotIndex);
         uint subpot = getSubpot(roundIndex);

         payable(winner).send(subpot);

         rounds[roundIndex].isCashed[subpotIndex] = true;
     }

     function getHashOfBlock(uint blockIndex) public view returns(uint){
         return uint(blockhash(blockIndex));
     }

     function getBuyers(uint roundIndex,address buyer) public view returns (address[] memory){
         return rounds[roundIndex].buyers;
     }

     function getTicketsCountByBuyer(uint roundIndex,address buyer) public view returns (uint){
         return rounds[roundIndex].ticketsCountByBuyer[buyer];
     }

     function getPot(uint roundIndex) public view returns(uint){
         return rounds[roundIndex].pot;
     }

     receive() external payable {

         uint roundIndex = getRoundIndex();
         uint value = msg.value-(msg.value%ticketPrice);

         if(value==0) return;

         if(value<msg.value){
             payable(msg.sender).send(msg.value-value);
         }

         uint ticketsCount = value/ticketPrice;
         rounds[roundIndex].ticketsCount+=ticketsCount;

         if(rounds[roundIndex].ticketsCountByBuyer[msg.sender]==0){
             rounds[roundIndex].buyers.push(msg.sender);
         }

         rounds[roundIndex].ticketsCountByBuyer[msg.sender]+=ticketsCount;
         rounds[roundIndex].ticketsCount+=ticketsCount;

         rounds[roundIndex].pot+=value;

     }

 }
