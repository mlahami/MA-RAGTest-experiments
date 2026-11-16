User Story: ERC20 Crowdfunding Campaigns

Title: Launch, Fund, Claim and Refund Time-Bound Crowdfunding Campaigns

As a campaign creator or a backer
I want to launch fundraising campaigns with a goal and a time window and pledge ERC20 tokens to them
So that creators collect the funds when the goal is reached and backers get their tokens back when it is not

Acceptance Criteria
1. Launch a Campaign
Given I am any user
When I call launch with a goal, startAt and endAt
Then startAt must be greater than or equal to the current time, otherwise the transaction reverts with "start at < now"
And endAt must be greater than or equal to startAt, otherwise it reverts with "end at < start at"
And endAt must not be more than 90 days from now, otherwise it reverts with "end at > max duration"
And count should increase by one and the campaign should be stored under the new id with me as creator, pledged 0 and claimed false
And a Launch event should be emitted with id, creator, goal, startAt and endAt
2. Cancel a Campaign
Given I created a campaign that has not started yet
When I call cancel with its id
Then the campaign should be deleted
And a Cancel event should be emitted
And if I am not the creator the transaction reverts with "not creator"
And if the campaign has already started it reverts with "started"
3. Pledge Tokens
Given a campaign is active (startAt <= now <= endAt) and I approved the tokens
When I call pledge with the id and an amount
Then the tokens should be transferred from me to the contract
And the campaign pledged total and my pledgedAmount should increase by the amount
And a Pledge event should be emitted
And before startAt the transaction reverts with "not started"; after endAt it reverts with "ended"
4. Unpledge Tokens
Given I pledged to a campaign that has not ended
When I call unpledge with the id and an amount
Then the amount should be returned to me
And the campaign pledged total and my pledgedAmount should decrease by the amount
And an Unpledge event should be emitted
And after endAt the transaction reverts with "ended"
And unpledging more than I pledged should fail
5. Claim Funds
Given I am the creator, the campaign has ended and pledged >= goal
When I call claim with the id
Then the full pledged amount should be transferred to me
And the campaign should be marked as claimed and a Claim event emitted
And the call reverts with "not creator", "not ended", "pledged < goal" or "claimed" when the respective condition is not met
6. Refund Pledges
Given the campaign has ended and pledged < goal
When I call refund with the id
Then my full pledged amount should be returned and my pledgedAmount reset to zero
And a Refund event should be emitted with the amount
And the call reverts with "not ended" before endAt and with "pledged >= goal" if the goal was reached

Notes
All campaigns use the single ERC20 token given to the constructor
Campaign ids start at 1
The test environment provides CrowdFundMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy the token passed to the CrowdFund constructor
