User Story: 14th Deposit Ether Prize Game

Title: Compete in a Fixed-Entry Ether Deposit Game to Win the Prize Pool

As a participant in a decentralized game
I want to deposit exactly 1 ETH per entry and compete to be the 14th depositor
So that I can win the entire accumulated Ether prize if I reach the target position

Acceptance Criteria
1. Join the Game
Given the game is active
When I send exactly 1 ETH to the contract
Then my deposit should be accepted
And the total game balance should increase by 1 ETH
And deposits must be rejected if the amount is not exactly 1 ETH
2. Enforce Game Limit
Given the game has a fixed target of 14 ETH total
When deposits are made
Then the total balance must not exceed 14 ETH
And any transaction that exceeds the limit should be rejected
And the game should stop once the target is reached
3. Determine Winner
Given the game reaches exactly 14 ETH total deposits
When the final valid deposit is made
Then the sender of that deposit should be recorded as the winner
4. Claim Prize
Given I am the recorded winner
When I call the claim function
Then I should receive the full contract balance
And the transfer must succeed or revert
5. Prevent Unauthorized Claims
Given I am not the winner
When I attempt to claim the reward
Then the transaction should fail
6. Check Contract Balance
Given I want to know the current prize pool
When I query the contract balance
Then I should receive the total Ether held by the contract
Notes
Each participant can only deposit exactly 1 ETH per transaction
The game ends once the total reaches 14 ETH
The winner is determined purely by deposit order, not timing or gas priority manipulation protections
There is no refund mechanism for failed or late participants
The contract is vulnerable to potential edge-case behaviors (e.g., force-sending ETH or front-running in real networks)