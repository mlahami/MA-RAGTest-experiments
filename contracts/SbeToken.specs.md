User Story: Mintable ERC20 Token with Authorized Minters

Title: Transfer, Approve and Mint a Fungible Token Controlled by Authorized Accounts

As a token holder or an authorized minter
I want to transfer tokens, delegate spending allowances and let authorized accounts mint new tokens
So that the token can be distributed (for example in an airdrop) while minting stays restricted

Acceptance Criteria
1. Deploy the Token
Given a name, symbol and decimals
When SbeToken is deployed
Then name, symbol and decimals should return the given values
And totalSupply should be zero
And the deployer should be authorized
2. Manage Authorized Accounts
Given I am authorized
When I call setAuthorized with an address and a boolean
Then that address's authorized status should be set to the boolean
And if I am not authorized the transaction reverts with "not authorized"
3. Mint Tokens
Given I am authorized
When I call mint with a recipient and an amount
Then the recipient balance and totalSupply should increase by the amount
And a Transfer event should be emitted from the zero address to the recipient
And if I am not authorized the transaction reverts with "not authorized"
4. Transfer Tokens
Given I hold tokens
When I call transfer with a recipient and an amount
Then my balance should decrease and the recipient balance increase by the amount
And a Transfer event should be emitted and the function returns true
And the transaction should fail if my balance is insufficient
5. Approve a Spender
Given I am a token holder
When I call approve with a spender and an amount
Then allowance(me, spender) should be set to the amount
And an Approval event should be emitted and the function returns true
6. Transfer on Behalf of Another Account
Given a sender approved me for an amount
When I call transferFrom with sender, recipient and amount
Then the allowance should decrease by the amount
And the sender balance should decrease and the recipient balance increase by the amount
And a Transfer event should be emitted and the function returns true
And the transaction should fail if the allowance or the sender balance is insufficient

Notes
Failed transfers revert rather than returning false
approve overwrites any previous allowance
Any authorized account can authorize or deauthorize other accounts, including itself
