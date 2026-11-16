User Story: Two-Token Swap Venue

Title: Swap Between Two Configured Tokens at a Price Given by the Venue's Token Balances

As a token holder
I want to swap one of two supported tokens for the other at a price derived from the venue's reserves
So that I can exchange tokens without a counterparty

Acceptance Criteria
1. Configure the Venue
Given I am the owner (the deployer)
When I call setTokens with two token addresses
Then token1 and token2 should be set
And a non-owner caller should be rejected by Ownable with OwnableUnauthorizedAccount
2. Add Liquidity
Given I am the owner and have approved the Dex for a token
When I call addLiquidity with the token address and an amount
Then that amount should be transferred from me to the Dex
And a non-owner caller should be rejected with OwnableUnauthorizedAccount
3. Quote a Swap
Given the Dex holds both tokens
When anyone calls getSwapPrice(from, to, amount)
Then it should return amount * (Dex balance of to) / (Dex balance of from), rounded down
4. Swap Tokens
Given I hold at least amount of from and have approved the Dex to spend it
When I call swap(from, to, amount) with from and to being token1 and token2 in either order
Then amount of from should move from me to the Dex
And getSwapPrice(from, to, amount) of to should move from the Dex to me
And the call should revert with "Invalid tokens" for any other token pair
And it should revert with "Not enough to swap" if my balance of from is below amount
5. Approve Both Tokens
Given token1 and token2 are configured
When I call approve(spender, amount) on the Dex
Then spender should be approved for amount of both token1 and token2 on my behalf
6. Read Balances
Given any token and account
When anyone calls balanceOf(token, account)
Then it should return that account's balance of the token

Notes
The file also contains the helper token SwappableToken (ERC20 minting its initial supply to the deployer, with an extra approve(owner, spender, amount) callable through the Dex); tests deploy two instances, call setTokens, add liquidity and give users tokens
Prices follow the Dex's current balances, so each swap changes the next quote
There are no fees and no events beyond the standard ERC20 Transfer and Approval events
