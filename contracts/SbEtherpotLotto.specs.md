User Story: Etherpot Round-Based Lottery

Title: Buy Lottery Tickets by Sending Ether and Cash Subpots After Each Round

As a lottery participant
I want to buy tickets by sending Ether, get refunds for partial tickets, and have subpot winners paid when a round ends
So that I can take part in a continuous, block-based lottery

Acceptance Criteria
1. Lottery Parameters
Given the contract is deployed
When anyone calls getBlocksPerRound, getTicketPrice or reads blocksPerRound, ticketPrice and blockReward
Then 6800 blocks per round, a ticket price of 0.1 ETH and a subpot size of 5 ETH should be returned
2. Buy Tickets
Given the current round index is the block number divided by 6800
When I send Ether to the contract
Then I should receive one ticket per full 0.1 ETH
And I should be added to the round's buyer list on my first purchase
And the round pot should increase by the ticket value
And sending less than 0.1 ETH should buy no tickets
3. Partial Ticket Refund
Given I send an amount that is not a multiple of 0.1 ETH
When the purchase is processed
Then the remainder should be refunded to me
And if the refund cannot be delivered the purchase should be reverted
4. Subpots
Given a round has a pot
When getSubpotsCount and getSubpot are called
Then the number of subpots should be the pot divided by 5 ETH, rounded up
And each subpot should be the pot divided by the subpot count
5. Determine a Winner
Given a round and subpot index
When calculateWinner is called after the decision block, which is the round end block plus the subpot index
Then the winner should be selected from the decision block hash modulo the round's ticket count, weighted by tickets per buyer
And before the decision block the zero address should be returned
6. Cash a Subpot
Given the decision block has passed and the subpot has not been cashed
When anyone calls cash with the round and subpot index
Then the subpot amount should be paid to the winner and the subpot marked as cashed
And if the payment to the winner fails the cash call should be reverted and the subpot must stay uncashed so it can be retried
And invalid indexes, early calls and already cashed subpots should do nothing
7. Queries
Given any user
When they call getRoundIndex, getIsCashed, getDecisionBlockNumber, getHashOfBlock, getBuyers, getTicketsCountByBuyer or getPot
Then the corresponding round information should be returned

Notes
There are infinitely many rounds
Each subpot can be cashed only once
