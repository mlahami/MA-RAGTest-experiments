User Story: 7th Deposit Ether Prize Game

Title: Deposit 1 ETH per Entry and Win the Pool by Making the Deposit That Reaches 7 ETH

As a participant in a deposit game
I want to deposit exactly 1 ETH per entry and become the winner if my deposit brings the pool to the target
So that I can claim the whole accumulated prize

Acceptance Criteria
1. Join the Game
Given the game pool is below TARGET_AMOUNT (7 ETH)
When I call deposit sending exactly 1 ETH
Then my deposit should be accepted
And the balance state variable should increase by 1 ETH
And the call should revert with "You can only send 1 Ether" if the amount is not exactly 1 ETH
2. Enforce the Target
Given the pool has already reached 7 ETH
When anyone calls deposit with 1 ETH
Then the call should revert with "Game is over"
3. Determine the Winner
Given the pool holds 6 ETH
When a participant makes a valid deposit
Then the pool should equal 7 ETH
And that participant should be recorded as winner
And earlier depositors should not be recorded as winner
4. Claim the Prize
Given I am the recorded winner
When I call claimReward
Then the balance state variable should be reset to 0
And I should receive the amount it held
And the call should revert with "Failed to send Ether" if the transfer fails
5. Prevent Unauthorized Claims
Given I am not the recorded winner
When I call claimReward
Then the call should revert with "Not winner"
6. Check the Pool
Given I want to know the current prize pool
When I read balance
Then I should receive the total deposited through deposit since the last claim

Notes
The game accounts only for Ether received through deposit, tracked in the balance state variable rather than the contract's raw Ether balance
The contract has no receive or fallback function, so plain Ether transfers are rejected
There is no refund mechanism for participants who do not win
