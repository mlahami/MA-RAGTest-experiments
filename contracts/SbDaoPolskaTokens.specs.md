User Story: DAO Polska Token Crowdsale

Title: Buy DPL Tokens During Funding, Transfer Them and Let the Owner Collect Raised Ether

As a crowdsale participant
I want to buy, transfer, burn or migrate DPL tokens and obtain refunds in refund state
So that I can join the community while the owner safely collects the funds raised

Acceptance Criteria
1. Deploy the Token
Given a deployer
When the contract is deployed with a migration agent address and a funding end block
Then the deployer should become owner and migration master
And name "DAO POLSKA TOKEN version 1", symbol "DPL", 18 decimals, zero total supply and funding enabled should be set
2. Buy Tokens
Given funding is enabled
When I call createDaoPOLSKAtokens for a holder with a non-zero value within the supply limit
Then the holder should receive value times CreationRate tokens and the Ether paid should be recorded
And an extra 12 percent should be minted to the migration master
And zero value, closed funding or exceeding the limit should revert
And plain Ether sent while funding should credit the sender's balance and emit receivedEther, otherwise revert
3. Token Operations
Given I hold tokens
When I call transfer, transferFrom, approve, approveAndCall, burn or burnFrom
Then balances, allowances and supply should update with matching events
And transfer and transferFrom should return false without changes when funds or allowance are insufficient
And burn and burnFrom should revert when balance or allowance is insufficient
4. Owner Configuration
Given I am the owner
When I call setSupply, setotherchainstotalsupply, setTokenInformation, setChainsAddresses, setBonusCreationRate, turnrefund or fundingState
Then the setting should change, emitting UpdatedTokenInformation for name changes
And setSupply should only work once
And other callers should be reverted, except setBonusCreationRate which ignores them
5. Owner Fund Collection
Given I am the owner
When I call PartialFundsTransfer with an amount to keep, or finalize after the funding end block plus eight weeks of blocks
Then the balance minus the kept amount, or the whole balance, should be sent to me
And finalize should stop funding and toggle the refund state
And if the payment to the owner fails the call should be reverted
And FundsTransfer should send the whole balance once funding has ended, reverting on failure
6. Migration and Refund
Given migration is not locked
When I call migrate with a positive amount up to my balance
Then my tokens should be removed, the migration agent notified and Migrate emitted
And when funding has ended and refund state is on, refundTRA should return my recorded Ether and emit Refund
7. Other Functions
Given the owner
When sendTokenAw is called
Then tokens of another token contract should be sent to a receiver

Notes
Regulation functions return fixed texts
