User Story: Constant Sum Automated Market Maker

Title: Swap Two Tokens at a One-to-One Rate and Provide Liquidity Using the x + y = k Rule

As a trader or liquidity provider
I want to exchange two ERC20 tokens of equal value at a fixed one-to-one rate minus a fee
So that I can trade stable pairs cheaply and earn a share of the pool by supplying liquidity

Acceptance Criteria
1. Deploy the Pool
Given two ERC20 token addresses
When the CSAMM contract is deployed with token0 and token1
Then token0 and token1 should be stored and readable
And reserve0, reserve1 and totalSupply should start at zero
2. Add Liquidity
Given I have approved both tokens to the pool
When I call addLiquidity with amount0 and amount1
Then both amounts should be transferred from me to the pool
And the deposited amounts d0 and d1 are measured as the increase of the pool balances over the stored reserves
And if totalSupply is zero I receive d0 + d1 shares
And otherwise I receive (d0 + d1) * totalSupply / (reserve0 + reserve1) shares
And if the computed shares are zero the transaction reverts with "shares = 0"
And reserve0 and reserve1 are updated to the new pool balances
3. Swap Tokens
Given the pool holds liquidity and I have approved the input token
When I call swap with tokenIn and amountIn
Then tokenIn must be token0 or token1, otherwise the transaction reverts with "invalid token"
And amountIn is transferred from me to the pool
And I receive amountOut = amountIn * 997 / 1000 of the other token
And the input reserve increases by amountIn and the output reserve decreases by amountOut
And the function returns amountOut
And the transaction should fail if the output reserve is smaller than amountOut
4. Remove Liquidity
Given I hold pool shares
When I call removeLiquidity with a number of shares
Then I should receive d0 = reserve0 * shares / totalSupply of token0 and d1 = reserve1 * shares / totalSupply of token1
And my shares and totalSupply should decrease by the burned shares
And the reserves should decrease by d0 and d1
And a token is only transferred if its amount is greater than zero
And the transaction should fail if I try to burn more shares than I own
5. Query Pool State
Given the pool is deployed
When I read reserve0, reserve1, totalSupply or balanceOf(account)
Then I should receive the current stored values

Notes
Both tokens are assumed to have the same decimals and value
A swap fee of 0.3% is deducted from the output amount
Shares are internal accounting values, not a transferable ERC20 token
The contract emits no events
The test environment provides CSAMMMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy token0 and token1, which are then passed to the CSAMM constructor
