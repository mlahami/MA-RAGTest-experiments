User Story: Double-or-Nothing Ether Lottery

Title: Place Ether Bets That Are Either Refunded or Kept by the Lottery

As a lottery player
I want to place an Ether bet that is either won or lost based on a chance outcome
So that I can try my luck and have my stake returned when I win

Acceptance Criteria
1. Deploy the Lottery
Given the SbLottery contract is deployed
When the deployment succeeds
Then the deployer should be recorded as the organizer
And the list of recorded bets should be empty
2. Place a Bet
Given the lottery is active
When I call makeBet and attach an Ether amount
Then a new bet should be recorded with my bet amount, the current block number and whether I won
And the outcome must be a fair coin flip that neither I nor any other participant can predict or select before sending the transaction
3. Winning Bet
Given my bet is a win
When the bet is processed
Then my stake should be sent back to me
And if the payment fails the whole transaction should revert so that no winning bet is recorded without being paid
4. Losing Bet
Given my bet is a loss
When the bet is processed
Then my stake should remain in the lottery contract
And the bet should still be recorded with won set to false
5. Review Bets
Given I am the organizer
When I call getBets
Then one GetBet event should be emitted for every recorded bet, in order, with its amount, block number and outcome
And if any other address calls getBets the transaction should revert
6. Destroy the Lottery
Given I am the organizer
When I call destroy
Then the contract should be closed and its full balance sent to me
And if any other address calls destroy the transaction should revert
7. Reject Direct Payments
Given someone sends Ether to the contract without calling makeBet
When the transfer is received
Then the transaction should revert

Notes
The list of bets is private; it is only exposed through the GetBet events
The organizer is fixed at deployment and cannot be changed
Each call to makeBet creates exactly one bet record
A bet of zero Ether is allowed and is recorded like any other bet
The probability of winning should be one half for every bet
