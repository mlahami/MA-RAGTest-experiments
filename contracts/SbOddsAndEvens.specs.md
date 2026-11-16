User Story: Odds and Evens Two-Player Game

Title: Bet 1 ETH on Whether the Sum of Two Numbers Is Even or Odd

As a player of a two-player betting game
I want to submit a number together with a 1 ETH stake and let the parity of the sum of both numbers decide the winner
So that the first player wins when the sum is even, the second player wins when it is odd, and the winner receives 1.8 ETH

Acceptance Criteria
1. Deploy the Game
Given the SbOddsAndEvens contract is deployed
When the deployment succeeds
Then the deployer should be recorded as the owner
And both player slots should be empty
2. Join as First Player
Given no player has joined the current round
When I call play with a number and exactly 1 ETH
Then I should be stored as player 0 with my number
And the transaction should revert if I send any amount other than 1 ETH
3. Join as Second Player
Given one player has joined the current round
When I call play with a number and exactly 1 ETH
Then I should be stored as player 1 with my number
And the winner should be determined immediately
4. Determine the Winner
Given two players have joined
When the round is settled
Then if the sum of both numbers is even, player 0 should receive 1.8 ETH
And if the sum is odd, player 1 should receive 1.8 ETH
And both player slots should be cleared so that a new round can start
5. Fair Play
Given the first player has already joined
When the second player chooses a number
Then the second player must not be able to learn the first player's number before committing their own
And neither player should be able to choose the outcome of the round
6. Collect Profit
Given I am the owner
When I call getProfit
Then the full contract balance, including the 0.2 ETH kept from each round, should be sent to me
And the transaction should revert if any other address calls it
7. Inspect Players
Given a round is in progress
When anyone reads players with index 0 or 1
Then the stored address and number for that slot should be returned

Notes
Each round needs exactly two players and two stakes of 1 ETH
The game keeps 0.2 ETH per completed round as profit for the owner
The same address may join both slots of a round
