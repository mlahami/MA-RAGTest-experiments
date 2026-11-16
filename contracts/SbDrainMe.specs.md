User Story: DrainMe Puzzle Game

Title: Join a Puzzle Game, Interact with Targets and Claim the Prize

As a puzzle player
I want to register as a player, use game actions and, if I become the winner, claim the contract balance
So that I can compete for the prize held by the contract

Acceptance Criteria
1. Deploy the Game
Given a deployer
When the contract is deployed with a first target and a second target address
Then both targets should be stored and publicly readable
And the seed list should start with two values and winner should be the zero address
2. Claim the Owner Role
Given any account
When it calls DranMe
Then it should become owner
3. Become a Player
Given any account
When it calls becomePlayer sending at least 0.02 ETH
Then it should be added to the players list and approved as a player
And lower amounts should be rejected
4. Player Actions
Given I am an approved player
When I call manipulateSecret with at least 0.01 ETH, setSeed, addSeed, guessSeed or checkSecret
Then the corresponding game action should run, with addSeed resizing the seed list and guessSeed returning my seed divided by the product of the first two seeds
And non-players should be rejected
5. Call the Targets
Given I am an approved player
When I call callFirstTarget or callSecondTarget sending at least 0.005 ETH
Then the full amount should be forwarded to the corresponding target
And if the target does not accept the payment the transaction should be reverted
And the amount must not remain in the contract after a failed forward
6. Owner Actions
Given I am the owner
When I call setSecret
Then the secret should be updated
And when I call winPrize, 1 wei should be sent to me, reverting if the payment fails
And non-owners should be rejected
7. Claim the Prize
Given I am the recorded winner
When I call claimPrize
Then the full contract balance should be transferred to me
And any other caller should be rejected
8. Views
Given any user
When they call getLength, getPlayerCount or getPrize
Then the seed count, player count and contract balance should be returned

Notes
The contract accepts plain Ether transfers to grow the prize
A player becomes winner when the hash of the previous block is divisible by five during manipulateSecret
Players remain approved permanently
