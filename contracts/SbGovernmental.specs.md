User Story: Governmental Jackpot Game

Title: Invest in the Jackpot and Win It If No One Invests for a Minute

As an investor
I want to invest at least half of the current jackpot and become the last investor
So that I win the whole jackpot if no further investment arrives within one minute

Acceptance Criteria
1. Establish the Game
Given the SbGovernmental contract is deployed with at least 1 ETH
When the deployment succeeds
Then the deployer should become the owner
And the jackpot should start at 1 ETH
And the deployment should revert if less than 1 ETH is sent
2. Invest
Given the game is running
When I call invest with at least half of the current jackpot
Then I should be recorded as the last investor
And half of my investment should be added to the jackpot
And the time of the last investment should be set to the current block time
And the call should revert if I send less than half of the current jackpot
3. Reset After Timeout
Given at least one minute has passed since the last investment
When anyone calls resetInvestment
Then the last investor should receive the jackpot
And the owner should receive the remaining balance above 1 ETH
And the last investor should be cleared, the jackpot reset to 1 ETH and the last investment time reset to 0
4. Reset Timing
Given less than one minute has passed since the last investment
When anyone calls resetInvestment
Then the transaction should revert and the game state should be unchanged
5. Read State
Given the game is running
When anyone reads owner, lastInvestor, jackpot, lastInvestmentTimestamp or ONE_MINUTE
Then the current values should be returned
6. Payout Timing Integrity
Given investments have been made
When the one-minute waiting period is evaluated
Then the reset must become available only after a full minute has genuinely elapsed since the last investment

Notes
The jackpot never drops below 1 ETH after a reset
Half of every investment is added to the jackpot and the rest stays in the contract
The waiting period before a reset is exactly one minute
Any address may trigger the reset once the waiting period has passed
