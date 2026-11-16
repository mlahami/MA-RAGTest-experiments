User Story: Predict the Block Hash Challenge

Title: Bet 1 ETH on the Hash of a Future Block

As a challenge player
I want to lock in a guess of the hash of the next block and later settle my guess
So that I win 2 ETH if my prediction of that block's hash is correct

Acceptance Criteria
1. Deploy and Fund the Challenge
Given the challenge owner deploys the SbPredictTheBlockHashChallenge contract
When exactly 1 ETH is sent with the deployment
Then the contract should be created holding 1 ETH
And the deployment should revert if any other amount is sent
2. Lock In a Guess
Given I have no active guess
When I call lockInGuess with a 32-byte hash and exactly 1 ETH
Then my guess should be stored
And the target block should be set to the block after the one containing my transaction
And the transaction should revert if I send any amount other than 1 ETH
And the transaction should revert if I already have an active guess
3. Settle a Guess
Given I have locked in a guess
When I call settle in a block later than my target block
Then the actual hash of my target block should be compared with my guess
And if they match I should receive 2 ETH
And if they do not match I should receive nothing
And in both cases my guess should be cleared so I can play again
4. Settlement Timing
Given I call settle
When the current block is not yet past my target block
Then the transaction should revert and my guess should remain active
5. Fair Outcome
Given the target block hash is only known after that block is produced
When a guess is settled
Then the outcome must depend on the real hash of the target block
And a guess must not be considered correct when the real hash of the target block can no longer be determined
And a player should not be able to win without actually predicting the hash
6. Settling Without a Guess
Given I never locked in a guess
When I call settle
Then I should not receive any payout

Notes
Each address can hold at most one active guess at a time
Guesses are private and have no getter function
The contract keeps the 1 ETH stakes of losing guesses
The prize of 2 ETH is paid only when the contract holds enough Ether; otherwise settle should revert
