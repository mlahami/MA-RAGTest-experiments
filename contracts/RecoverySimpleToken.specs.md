User Story: Simple Ether-Backed Token

Title: Buy, Hold and Transfer a Simple Token Backed by Ether

As a token holder
I want to obtain tokens by sending Ether and transfer them to other accounts
So that I can use a simple named token whose balances are tracked on chain

Acceptance Criteria
1. Initialize the Token
Given the contract is deployed with a name, a creator address and an initial supply
When the constructor runs
Then name should be set to the given name
And the creator's balance should be equal to the initial supply
2. Buy Tokens with Ether
Given I hold some Ether
When I send Ether to the contract with empty calldata
Then the Ether should be accepted
And my token balance should increase by 10 tokens for every wei sent
And repeated purchases should accumulate on my balance
3. Transfer Tokens
Given I have a token balance of at least the amount
When I call transfer with a recipient and an amount
Then my balance should decrease by the amount
And the recipient's balance should increase by the amount
And the sum of my balance and the recipient's balance should be preserved
4. Reject Transfers Above Balance
Given my balance is smaller than the amount
When I call transfer
Then the transaction should revert
And no balance should change
5. Recover the Contract Funds
Given the contract holds Ether
When destroy is called with a payable destination address
Then the entire Ether balance of the contract should be sent to the destination address
6. Read Balances and Name
Given any account
When I query balances(address) or name
Then I should receive the stored balance and the token name
Notes
There is no total supply variable and no events are emitted
The transfer revert has no message
Tokens are created only at deployment and when Ether is received
