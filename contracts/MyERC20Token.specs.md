User Story: Standard ERC-20 Token Transfer and Approval System

Title: Create and Manage a Fungible Token with Transfer and Allowance Mechanisms

As a token holder
I want to transfer tokens, approve spenders, and allow delegated transfers
So that I can participate in a standard ERC-20 token ecosystem with controlled spending

Acceptance Criteria
1. Token Initialization
Given the contract is deployed
When deployment completes
Then the total supply should be assigned entirely to the deployer
And no additional tokens can be minted
2. Check Total Supply
Given the token exists
When I query total supply
Then I should receive a fixed constant value representing all existing tokens
3. Check Account Balance
Given any address holds tokens
When I query its balance
Then I should receive the correct token amount stored in the mapping
4. Transfer Tokens
Given I hold enough tokens
When I transfer tokens to another address
Then:
My balance should decrease
Recipient balance should increase
A Transfer event should be emitted
And transfers should only succeed if:
Value is greater than zero
Sender has sufficient balance
5. Approve Spender
Given I want to allow another address to spend my tokens
When I call approve with a spender and value
Then the allowance should be recorded
And an Approval event should be emitted
6. Check Allowance
Given a spender has been approved
When I check allowance
Then I should see the remaining approved amount
7. Delegated Transfer (transferFrom)
Given a spender has allowance from a token owner
When the spender calls transferFrom
Then tokens should be transferred from owner to recipient
And the transfer should only succeed if:
Allowance is sufficient
Value is greater than zero
Recipient is not a smart contract (as enforced by this implementation)
8. Contract Detection Restriction
Given a transferFrom call is made
When the recipient is a smart contract
Then the transfer should be rejected
Notes
This is a simplified ERC-20 implementation, not fully compliant with the standard
Missing features include:
No allowance decrement after transferFrom
No SafeMath usage (but Solidity 0.8+ handles overflow protection)
No minting or burning functionality
Unusual restriction preventing transfers to smart contracts
Token supply is fixed at deployment
All tokens are initially assigned to the deployer