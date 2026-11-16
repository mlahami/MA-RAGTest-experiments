User Story: Basic ERC20 Token With Allowances

Title: Transfer Tokens and Delegate Spending Through Allowances

As a token holder
I want to transfer my tokens and authorise other accounts to spend a limited amount on my behalf
So that I can pay others directly or let applications move tokens for me within limits I control

Acceptance Criteria
1. Deploy the Token
Given the SbERC20 contract is deployed with an initial supply value
When the deployment succeeds
Then the deployer's balance should equal the initial supply
And every other address should have a balance of 0
2. Query Balances and Allowances
Given the token is deployed
When anyone calls balanceOf for an address or allowance for an owner and a spender
Then the current balance or remaining allowance should be returned
3. Transfer Tokens
Given I hold tokens
When I call transfer with a non-zero receiver and an amount not above my balance
Then my balance should decrease and the receiver's balance increase by that amount
And a Transfer event should be emitted and the call return true
And the call should revert if the amount exceeds my balance or the receiver is the zero address
4. Approve a Spender
Given I want to authorise a spender
When I call approve with a non-zero spender address and an amount
Then the allowance for that spender should be set to the amount
And an Approval event should be emitted and the call return true
And the call should revert if the spender is the zero address
And when I change an existing non-zero allowance, the spender must not be able to spend more in total than the larger of the old and the new allowance
5. Spend an Allowance
Given a spender has an allowance from me
When the spender calls transferFrom with my address, a non-zero receiver and an amount within both the allowance and my balance
Then the tokens should move from me to the receiver
And the allowance should decrease by the amount
And a Transfer event should be emitted and the call return true
And the call should revert if the amount exceeds the allowance or my balance, or the receiver is the zero address
6. Arithmetic Safety
Given any balance or allowance update
When amounts are added or subtracted
Then results must never wrap around; invalid operations should revert

Notes
The token has no name, symbol, decimals, minting or burning
The total supply is not exposed through a getter
Allowances are tracked per owner and per spender
