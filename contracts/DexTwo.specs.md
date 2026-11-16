User Story: Token Swap Venue

Title: Swap Tokens at a Price Given by the Venue's Token Balances

As a token holder
I want to swap a token I hold for another token held by the venue at a price derived from the venue's reserves
So that I can exchange tokens without a counterparty

Acceptance Criteria
1. Configure the Venue
Given I am the owner (the deployer)
When I call setTokens with two token addresses
Then token1 and token2 should be set
And a non-owner caller should be rejected by Ownable with OwnableUnauthorizedAccount
2. Add Liquidity
Given I am the owner and have approved DexTwo for a token
When I call add_liquidity with the token address and an amount
Then that amount should be transferred from me to DexTwo
And a non-owner caller should be rejected with OwnableUnauthorizedAccount
3. Quote a Swap
Given DexTwo holds some of both tokens
When anyone calls getSwapAmount(from, to, amount)
Then it should return amount * (DexTwo balance of to) / (DexTwo balance of from), rounded down
4. Swap Tokens
Given I hold at least amount of the from token and have approved DexTwo to spend it
When I call swap(from, to, amount) with any ERC20 token addresses from and to
Then amount of from should move from me to DexTwo
And getSwapAmount(from, to, amount) of to should move from DexTwo to me
And the call should revert with "Not enough to swap" if my balance of from is below amount
5. Approve Both Tokens
Given token1 and token2 are configured
When I call approve(spender, amount) on DexTwo
Then spender should be approved for amount of both token1 and token2 on my behalf
6. Read Balances
Given any token and account
When anyone calls balanceOf(token, account)
Then it should return that account's balance of the token

Notes
The file also contains the helper token SwappableTokenTwo (ERC20 minting its initial supply to the deployer, with an extra approve(owner, spender, amount) callable through DexTwo); tests deploy two instances, call setTokens, add liquidity and give users tokens
Swaps are intended to take place only between the two listed tokens, token1 and token2
Prices follow DexTwo's current balances, so each swap changes the next quote
There are no fees and no events beyond the standard ERC20 Transfer and Approval events
