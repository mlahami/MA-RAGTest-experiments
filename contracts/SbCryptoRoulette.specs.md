User Story: Crypto Roulette Number Guessing Game

Title: Guess the Secret Number and Win the Whole Contract Balance

As a player
I want to pay a bet and guess the secret number stored in the contract
So that I win the entire contract balance when my guess matches the secret number

Acceptance Criteria
1. Deploy the Game
Given the SbCryptoRoulette contract is deployed
When the deployment succeeds
Then the deployer should be stored as ownerAddr
And betPrice should be 0.1 ETH
And a secret number between 1 and 20 should be chosen
2. Fund the Prize
Given the game is deployed
When anyone sends Ether directly to the contract
Then the Ether should be accepted and added to the prize balance
3. Play a Round
Given I want to guess the secret number
When I call play with a number up to 10 and at least betPrice
Then a game record with my address and my number should be appended to gamesPlayed
And if my number equals the current secret number, the whole contract balance should be transferred to me
And a new secret number between 1 and 20 should then be chosen
And lastPlayed should be set to the current block timestamp
And the transaction should revert if I send less than betPrice or guess a number greater than 10
4. Game Integrity
Given a round is played
When the game record is stored
Then storing the record must not alter the secret number, lastPlayed, betPrice or ownerAddr
And a player who guesses the current secret number must always win
5. Read Game History
Given rounds have been played
When anyone reads gamesPlayed with an index
Then the player address and the guessed number of that round should be returned
And lastPlayed should return the time of the latest round
6. Close the Game
Given I am the owner
When I call kill more than one day after the last round
Then the contract should be closed and its balance sent to me
And calls from other addresses, or within one day of the last round, should have no effect

Notes
The secret number is private and has no getter
Each round costs at least 0.1 ETH and the stake stays in the prize pool if the guess is wrong
The secret changes after every round
Guesses above 10 are rejected even though the secret can range up to 20
