User Story: Basic Mintable ERC20 Token

Title: Mint, Transfer, Approve and Burn a Basic ERC20 Token

As a token user
I want to mint my own tokens, transfer them, delegate spending through allowances and burn them
So that I can use a simple ERC20-compatible token with accurate balances and supply

Acceptance Criteria
1. Token Metadata
Given the DvlERC20 contract is deployed
When I query name, symbol and decimals
Then I should receive "Test example", "Test" and 18
And totalSupply should initially be 0
2. Mint Tokens
Given any account
When I call mint with an amount
Then my balanceOf should increase by the amount
And totalSupply should increase by the amount
And a Transfer event should be emitted from address(0) to me with the amount
3. Transfer Tokens
Given my balance is at least amount
When I call transfer with a recipient and amount
Then my balance should decrease by amount and the recipient's balance should increase by amount
And a Transfer event should be emitted and the call should return true
And if my balance is lower than amount, the transaction should revert
4. Approve a Spender
Given I am a token holder
When I call approve with a spender and an amount
Then allowance[me][spender] should be set to that amount, replacing any previous value
And an Approval event should be emitted and the call should return true
5. Transfer on Behalf of Another Account
Given the sender has approved me for at least amount and holds at least amount
When I call transferFrom with sender, recipient and amount
Then the allowance should decrease by amount
And the sender's balance should decrease by amount and the recipient's balance should increase by amount
And a Transfer event from sender to recipient should be emitted and the call should return true
And if the allowance or the sender's balance is insufficient, the transaction should revert
6. Burn Tokens
Given my balance is at least amount
When I call burn with amount
Then my balance and totalSupply should both decrease by amount
And a Transfer event should be emitted from me to address(0)
And if my balance is lower than amount, the transaction should revert
Notes
Anyone can mint tokens for themselves; there is no owner role
A transfer with insufficient balance or allowance fails without a custom error message
Total supply always equals the sum of minted minus burned amounts
