User Story: Constant Product Automated Market Maker

Title: Swap Between Two Tokens and Provide Liquidity Using the x * y = k Pricing Rule

As a liquidity provider or trader
I want to deposit a pair of ERC20 tokens into a pool and swap one token for the other
So that I can earn a share of the pool and exchange tokens at a price set by the pool reserves

Acceptance Criteria
1. Deploy the Pool
Given two ERC20 token addresses
When the CPAMM contract is deployed with token0 and token1
Then token0 and token1 should be stored and readable
And reserve0, reserve1 and totalSupply should start at zero
2. Add Initial Liquidity
Given the pool is empty and I have approved both tokens to the pool
When I call addLiquidity with amount0 and amount1
Then both amounts should be transferred from me to the pool
And I should receive shares equal to the integer square root of amount0 * amount1
And balanceOf for me and totalSupply should increase by those shares
And reserve0 and reserve1 should equal the pool's token balances
3. Add Further Liquidity
Given the pool already holds reserves
When I call addLiquidity
Then the deposit ratio must match the reserve ratio (reserve0 * amount1 == reserve1 * amount0), otherwise the transaction reverts with "x / y != dx / dy"
And I should receive the minimum of amount0 * totalSupply / reserve0 and amount1 * totalSupply / reserve1 as shares
And if the computed shares are zero the transaction reverts with "shares = 0"
4. Swap Tokens
Given the pool holds liquidity and I have approved the input token
When I call swap with tokenIn and amountIn
Then tokenIn must be token0 or token1, otherwise the transaction reverts with "invalid token"
And amountIn must be greater than zero, otherwise it reverts with "amount in = 0"
And amountIn is transferred from me to the pool
And I receive amountOut = reserveOut * amountInWithFee / (reserveIn + amountInWithFee), where amountInWithFee = amountIn * 997 / 1000
And the reserves are updated to the pool's token balances
And the function returns amountOut
5. Remove Liquidity
Given I hold pool shares
When I call removeLiquidity with a number of shares
Then I should receive amount0 = shares * balance0 / totalSupply and amount1 = shares * balance1 / totalSupply
And if either amount is zero the transaction reverts with "amount0 or amount1 = 0"
And my shares and totalSupply should decrease by the burned shares
And the reserves should decrease by the withdrawn amounts
And the transaction should fail if I try to burn more shares than I own
6. Query Pool State
Given the pool is deployed
When I read reserve0, reserve1, totalSupply or balanceOf(account)
Then I should receive the current stored values

Notes
A swap fee of 0.3% is applied to the input amount and stays in the pool
Shares are internal accounting values, not a transferable ERC20 token
The contract emits no events
The test environment provides CPAMMMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy token0 and token1, which are then passed to the CPAMM constructor
