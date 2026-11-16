User Story: Time-Based Staking Rewards

Title: Stake Tokens and Earn Rewards Streamed at a Fixed Rate Over a Reward Period

As a token holder or reward administrator
I want to stake ERC20 tokens and earn reward tokens per second in proportion to my stake
So that rewards set by the owner are shared fairly among stakers over the reward period

Acceptance Criteria
1. Deploy the Contract
Given a staking token and a rewards token
When StakingRewards is deployed with stakingToken and rewardToken
Then the deployer should be recorded as owner
And both token addresses should be stored and readable
2. Set the Reward Duration
Given I am the owner and the current reward period has finished
When I call setRewardsDuration with a duration
Then duration should be updated
And if I am not the owner the transaction reverts with "not authorized"
And if the current period is still running it reverts with "reward duration not finished"
3. Start or Extend a Reward Period
Given I am the owner, duration is set and the contract holds enough reward tokens
When I call notifyRewardAmount with an amount
Then if the previous period ended rewardRate becomes amount / duration
And otherwise rewardRate becomes (amount + remaining rewards) / duration
And finishAt becomes now + duration and updatedAt becomes now
And the call reverts with "reward rate = 0" if the rate is zero and with "reward amount > balance" if rewardRate * duration exceeds the reward token balance
And non-owners are rejected with "not authorized"
4. Stake Tokens
Given I approved the staking token
When I call stake with an amount greater than zero
Then my accrued rewards are updated first
And the amount is transferred to the contract and my balanceOf and totalSupply increase
And an amount of zero reverts with "amount = 0"
5. Withdraw Staked Tokens
Given I have staked tokens
When I call withdraw with an amount greater than zero
Then my accrued rewards are updated, my balanceOf and totalSupply decrease and the tokens are returned
And an amount of zero reverts with "amount = 0"; withdrawing more than my balance fails
6. Claim Rewards
Given I have earned rewards
When I call getReward
Then my rewards are transferred to me and reset to zero
And nothing is transferred if I have no rewards
7. Query Reward Data
Given the contract is deployed
When I call lastTimeRewardApplicable, rewardPerToken or earned(account)
Then I receive min(finishAt, now), the accumulated reward per staked token (scaled by 1e18), and the account's total claimable rewards

Notes
Rewards are computed per second of staking duration and stop accruing at finishAt
The reward tokens must be sent to the contract before notifyRewardAmount is called
The contract emits no events
The test environment provides StakingRewardsMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy the staking and rewards tokens passed to the constructor
