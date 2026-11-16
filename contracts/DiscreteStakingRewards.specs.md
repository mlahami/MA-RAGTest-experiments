User Story: Discrete Staking Rewards

Title: Stake Tokens and Receive a Proportional Share of Each Reward Distribution

As a token holder
I want to stake ERC20 tokens and receive a share of every reward deposit in proportion to my stake
So that I am rewarded for each distribution that happens while my tokens are staked

Acceptance Criteria
1. Deploy the Staking Contract
Given a staking token and a reward token
When DiscreteStakingRewards is deployed with stakingToken and rewardToken
Then both token addresses should be stored and readable
And totalSupply should start at zero
2. Stake Tokens
Given I have approved the staking token
When I call stake with an amount
Then my rewards earned so far should be recorded first
And my balanceOf and totalSupply should increase by the amount
And the amount should be transferred from me to the contract
3. Distribute Rewards
Given at least one user has staked tokens and I approved the reward token
When I call updateRewardIndex with a reward amount
Then the reward should be transferred from me to the contract
And the reward index should increase by reward * 1e18 / totalSupply
And every current staker becomes entitled to reward * balanceOf / totalSupply
And the call should fail if totalSupply is zero
4. Check Earned Rewards
Given I have staked tokens
When I call calculateRewardsEarned with my address
Then I should receive my recorded rewards plus the rewards accrued since my last update
5. Unstake Tokens
Given I have staked tokens
When I call unstake with an amount
Then my rewards earned so far should be recorded first
And my balanceOf and totalSupply should decrease by the amount
And the amount should be transferred back to me
And unstaking more than my balance should fail
6. Claim Rewards
Given I have earned rewards
When I call claim
Then my pending rewards should be recorded and transferred to me in reward tokens
And my earned balance should be reset to zero
And the function should return the claimed amount
And if I have no rewards nothing is transferred and zero is returned

Notes
Rewards are distributed in discrete deposits, not continuously over time
Users who stake after a distribution do not receive a share of it
Anyone may call updateRewardIndex to add rewards
The contract emits no events
The test environment provides DiscreteStakingRewardsMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy the staking and reward tokens passed to the constructor
