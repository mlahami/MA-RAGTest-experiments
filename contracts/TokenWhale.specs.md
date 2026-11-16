User Story: Simple ERC20 Token with Approve-and-Call

Title: Transfer, Approve and Delegate Spending of a Simple Token

As a holder of the Simple ERC20 Token (SET)
I want to transfer tokens, approve spenders, let them transfer on my behalf and notify them on approval
So that balances and allowances stay accurate for every account

Acceptance Criteria
1. Initialize the Token
Given the TokenWhale contract is deployed
When TokenWhaleDeploy(player) is called
Then totalSupply should be 1000
And the player's balance should be 1000
And name, symbol and decimals should be "Simple ERC20 Token", "SET" and 18
2. Check the Player Goal
Given the token is initialized
When I call isComplete
Then it should return true only if the player's balance is at least 1000000
And it should return false right after initialization
3. Transfer Tokens
Given my balance is at least value
When I call transfer(to, value)
Then my balance should decrease by value and to's balance should increase by value
And a Transfer event from me to to should be emitted
And if my balance is lower than value, the transaction should revert
4. Approve a Spender
Given I am a token holder
When I call approve(spender, value)
Then allowance[me][spender] should be set to value
And an Approval event should be emitted
5. Transfer on Behalf of an Owner
Given from has at least value tokens and has approved me for at least value
When I call transferFrom(from, to, value)
Then allowance[from][me] should decrease by value
And from's balance should decrease by value and to's balance should increase by value
And a Transfer event from from to to should be emitted
And my own balance should not change
And the call should revert if from's balance or my allowance is insufficient
6. Approve and Call
Given I want to approve a spender and notify it in one step
When I call approveAndCallcode(spender, value, extraData)
Then allowance[me][spender] should be set to value
And the spender should be called with extraData
Notes
The total supply is fixed at 1000 after initialization; there is no mint or burn
The result of the call in approveAndCallcode does not affect the approval
Revert conditions have no messages
