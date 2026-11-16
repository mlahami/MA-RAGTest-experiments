User Story: ETH and WETH Staking Pool

Title: Stake ETH or WETH and Unstake to Recover Funds

As a staker
I want to deposit ETH or WETH into a staking pool and withdraw my stake later
So that my stake is tracked and the pool's total staked amount is accurate

Acceptance Criteria
1. Deploy the Pool
Given the pool is deployed with the address of the WETH token, optionally with Ether attached
When the constructor runs
Then WETH should be set to the given address
And totalStaked should equal the Ether sent at deployment
2. Stake ETH
Given I send more than 0.001 ether
When I call StakeETH
Then totalStaked and UserStake[me] should both increase by msg.value
And Stakers[me] should become true
And if msg.value is 0.001 ether or less, the call should revert with "Don't be cheap"
3. Stake WETH
Given I have approved the pool to spend at least amount WETH and I hold that amount
When I call StakeWETH with an amount greater than 0.001 ether
Then the WETH should be transferred from me to the pool
And totalStaked and UserStake[me] should both increase by amount
And Stakers[me] should become true and the call should return true
4. Reject Invalid WETH Stakes
Given I call StakeWETH
When amount is 0.001 ether or less
Then the call should revert with "Don't be cheap"
And when my allowance to the pool is below amount, it should revert with "How am I moving the funds honey?"
And when the WETH transfer to the pool does not succeed, my stake and totalStaked should not be increased
5. Unstake
Given UserStake[me] is at least amount
When I call Unstake with amount
Then UserStake[me] and totalStaked should both decrease by amount
And amount should be sent to me in ETH
And the call should return true when the payment succeeds
6. Reject Excessive Unstake
Given UserStake[me] is smaller than amount
When I call Unstake
Then the call should revert with "Don't be greedy"
7. Read the State
Given any account
When I query totalStaked, UserStake, Stakers or WETH
Then I should receive the current values
Notes
StakeMockToken is a helper ERC20 in the same file (configurable decimals, public mint); tests deploy it and pass its address as WETH
Stakers stays true after unstaking
No events are emitted
