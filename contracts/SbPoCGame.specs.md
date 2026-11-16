User Story: Fixed-Wager Block Game with Charity Donations

Title: Wager a Fixed Amount, Play Against a Block Hash and Support a Whale Charity

As a player of an on-chain chance game
I want to place a fixed wager, play it in a later block and have losing wagers partly donated to a charity contract
So that I can win half of the prize pool while donations reliably reach the charity

Acceptance Criteria
1. Deploy the Game
Given a deployer that is an externally owned account
When the contract is deployed with a whale (charity) address and a wager limit
Then the deployer should become the owner
And deployment from a contract account should be rejected
2. Owner Administration
Given I am the owner
When I open the game to the public, adjust the bet amount or adjust the difficulty
Then the corresponding setting should be updated
And BetLimitChanged or DifficultyChanged should be emitted with the new value
And any non-owner calling these functions should be rejected
3. Place a Wager
Given the game is open
When I call wager from an externally owned account sending exactly the bet limit
Then my wager and the current block number should be recorded
And a Wager event should be emitted
And the call should be rejected if the game is closed, the amount differs from the bet limit, or I already have an open wager
4. Play a Wager
Given I have an open wager placed in an earlier block
When I call play
Then my wager should be cleared
And if the computed winning number equals half the difficulty I should receive half of the contract balance and a Win event should be emitted
And otherwise half of the bet limit should be forwarded to the whale by calling its donate function, total donations should increase and a Lose event should be emitted
And play in the same block as the wager, or without an open wager, should be rejected
5. Donate
Given the game is open
When I call donate with Ether
Then the full amount should be forwarded to the whale's donate function
And total donations should increase and a Donate event should be emitted
6. Reliable Forwarding
Given the whale contract rejects a forwarded donation
When donate or a losing play is processed
Then the whole transaction should be reverted
And no donation should be recorded
7. Views and Token Recovery
Given any user
When they call ethBalance, currentDifficulty, currentBetLimit, hasPlayerWagered or winnersPot
Then the corresponding values should be returned
And only the owner may call transferAnyERC20Token

Notes
The contract accepts plain Ether transfers to grow the prize pool
The difficulty must be set before play can succeed
