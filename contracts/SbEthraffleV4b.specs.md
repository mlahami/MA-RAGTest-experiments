User Story: Ether Raffle With Fixed Number of Tickets

Title: Buy Raffle Tickets and Win a Fixed Prize When All Tickets Are Sold

As a raffle participant
I want to buy one or more tickets for the current raffle and get refunds while the raffle is still open
So that I have a fair chance to win the 2.5 ETH prize once all 50 tickets are sold

Acceptance Criteria
1. Raffle Configuration
Given the SbEthraffleV4b contract is deployed
When I read its public values
Then prize should be 2.5 ETH, fee 0.03 ETH, totalTickets 50 and pricePerTicket (prize + fee) / 50
And raffleId should start at 1 and paused should be false
And the deployer should be the fee collector
2. Buy Tickets
Given the raffle is not paused
When I call buyTickets, or send Ether directly to the contract
Then I should receive as many tickets as my payment covers, up to the remaining tickets, reusing refunded ticket numbers first
And a TicketPurchase event should be emitted per ticket
And any amount left over should be returned to me
And if the raffle is paused my whole payment should be returned
3. Draw the Winner
Given the last of the 50 tickets is bought
When the purchase completes
Then a winner should be chosen among the ticket holders in a way no participant, miner or caller can predict or influence
And the winner should receive the prize, the fee collector the fee, and a RaffleResult event be emitted
And a new raffle should start with raffleId increased by 1 and blockNumber updated
4. Refund
Given I hold tickets in the current raffle
When I call getRefund
Then each of my tickets should be released, a TicketRefund event emitted per ticket, and the ticket price returned to me
And calling it with no tickets should transfer nothing
5. End the Raffle
Given I am the fee collector
When I call endRaffle
Then every ticket of the current raffle should be refunded, the raffle should be paused and a new raffleId started
And calls by other addresses should have no effect
6. Pause and Close
Given I am the fee collector
When I call togglePause the paused flag should switch
And when I call kill the contract should be closed and its balance sent to me
And both calls should have no effect for other addresses

Notes
Tickets are identified by numbers 0 to 49 within each raffle
The winner selection is triggered automatically by the purchase of the final ticket
