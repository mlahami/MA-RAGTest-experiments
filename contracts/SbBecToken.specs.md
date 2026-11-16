User Story: BeautyChain Pausable Token With Batch Transfers

Title: Hold, Transfer and Batch-Distribute BEC Tokens Under Owner Pause Control

As a holder of BeautyChain (BEC) tokens
I want to transfer tokens individually, approve spenders and send the same amount to several receivers in one transaction
So that I can distribute tokens efficiently while the owner can pause activity in an emergency

Acceptance Criteria
1. Deploy the Token
Given the SbBecToken contract is deployed
When the deployment succeeds
Then name should be "BeautyChain", symbol "BEC", version "1.0.0" and decimals 18
And totalSupply should equal 7,000,000,000 tokens with 18 decimals
And the deployer should own the whole supply and become the owner
2. Transfer Tokens
Given I hold tokens and the token is not paused
When I call transfer with a non-zero receiver and an amount greater than 0 and not above my balance
Then my balance should decrease and the receiver's increase by that amount
And a Transfer event should be emitted
And the call should revert for the zero address, a zero amount or an amount above my balance
3. Approve and Transfer From
Given the token is not paused
When I call approve for a spender, and the spender later calls transferFrom within the allowance and my balance
Then the tokens should move, the allowance should decrease, and Approval and Transfer events should be emitted
And transferFrom should revert when the amount exceeds the allowance or the balance, is zero, or the receiver is the zero address
4. Batch Transfer
Given the token is not paused
When I call batchTransfer with between 1 and 20 receivers and a value greater than 0
Then the total amount debited from me must equal the number of receivers multiplied by the value
And each receiver should be credited exactly the value, with one Transfer event per receiver
And the call should revert if that total exceeds my balance, if the list is empty or longer than 20, or if the value is zero
And the total supply must never change through transfers
5. Pause and Unpause
Given I am the owner
When I call pause, every transfer, transferFrom, approve and batchTransfer should revert until I call unpause
And Pause and Unpause events should be emitted
And pause and unpause should revert for non-owners or when already in the requested state
6. Ownership
Given I am the owner
When I call transferOwnership with a non-zero address
Then ownership should move and OwnershipTransferred be emitted
And the call should revert for non-owners or the zero address

Notes
balanceOf and allowance are read-only queries
Plain Ether sent to the token must be rejected
