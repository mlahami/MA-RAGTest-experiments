User Story: Three-Token Stable Swap Pool

Title: Swap and Provide Liquidity Across Three Stablecoins Using the Curve StableSwap Invariant

As a stablecoin trader or liquidity provider
I want to swap between three pegged tokens with low slippage and deposit or withdraw liquidity
So that I can exchange stablecoins near parity and earn fees as a liquidity provider

Acceptance Criteria
1. Deploy the Pool
Given three ERC20 token addresses
When StableSwap is deployed with the array of three tokens
Then tokens(0), tokens(1) and tokens(2) should return those addresses
And balances and totalSupply should start at zero
2. Add Liquidity
Given I approved the tokens I want to deposit
When I call addLiquidity with three amounts and minShares
Then each non-zero amount should be transferred from me to the pool
And the pool invariant D must increase, otherwise the transaction reverts with "liquidity didn't increase"
And on the first deposit I receive shares equal to the new D
And on later deposits I receive (D2 - D0) * totalSupply / D0 shares, where D2 includes a fee on imbalanced deposits
And balances should increase by the deposited amounts
And if shares < minShares the transaction reverts with "shares < min"
3. Swap Tokens
Given the pool holds liquidity and I approved token i
When I call swap with i, j, dx and minDy
Then i must differ from j, otherwise it reverts with "i = j"
And dx of token i is transferred from me to the pool
And I receive dy of token j computed from the invariant, minus a 0.03% swap fee
And if dy < minDy the transaction reverts with "dy < min"
And balances[i] increases by dx and balances[j] decreases by dy
4. Remove Liquidity Proportionally
Given I hold shares
When I call removeLiquidity with shares and three minimum amounts
Then for each token I receive balances[i] * shares / totalSupply
And if any amount is below its minimum the transaction reverts with "out < min"
And balances, my shares and totalSupply should decrease accordingly
5. Remove Liquidity in One Token
Given I hold shares
When I call removeLiquidityOneToken with shares, index i and minAmountOut
Then I receive the amount given by calcWithdrawOneToken for token i
And if it is below minAmountOut the transaction reverts with "out < min"
And balances[i], my shares and totalSupply should decrease
6. Query Prices and Estimates
Given the pool is deployed
When I call getVirtualPrice
Then I receive D * 1e18 / totalSupply, or 0 when totalSupply is zero
And calcWithdrawOneToken(shares, i) returns the withdrawable amount and fee without changing state

Notes
The pool assumes token 0 has 18 decimals and tokens 1 and 2 have 6 decimals; amounts are normalised to 18 decimals internally
Amplification coefficient A = 1000 * N^(N-1) with N = 3
The swap fee is 300 / 1e6; imbalanced liquidity operations pay a smaller liquidity fee
Shares are internal accounting values, not a transferable ERC20 token; the contract emits no events
The test environment provides StableSwapMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy the three tokens, with decimals 18, 6 and 6, passed to the StableSwap constructor
