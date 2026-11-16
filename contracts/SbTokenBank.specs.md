User Story: Token Bank With Owner-Controlled Withdrawals

Title: Deposit Ether and Let the Owner Return Ether or Move ERC20 Tokens to Holders

As the owner of a token bank
I want customers to deposit Ether and be recorded as holders, and to return Ether or move ERC20 tokens to them under my control
So that deposits are tracked per holder and only I can trigger withdrawals

Acceptance Criteria
1. Deploy and Initialise
Given the SbTokenBank contract is deployed
When I call initTokenBank
Then I should become the owner
And MinDeposit should be set to 1 ETH
2. Transfer Ownership
Given I am the owner
When I call changeOwner with a new address, and that address then calls confirmOwner
Then the new address should become the owner
And changeOwner should have no effect when called by a non-owner
3. Deposit Ether
Given the bank is deployed
When I call Deposit with more than MinDeposit, or send Ether directly to the bank
Then my recorded holding in Holders should increase by the amount sent
And a deposit of MinDeposit or less should not change my holding
4. Withdraw Ether to a Holder
Given I am the owner and a holder has a positive holding
When I call WithdrawToHolder with the holder address and an amount of wei
Then the amount should be sent to the holder
And the holder's recorded holding should be reduced by exactly that amount
And the call should have no effect for non-owners or for a holder with a zero holding
5. Withdraw Tokens to a Holder
Given I am the owner and a holder has a positive holding
When I call WitdrawTokenToHolder with the holder, a token contract and an amount
Then the holder's recorded holding should be set to zero
And a token transfer of that amount to the holder should be requested from the token contract
And the call should have no effect for non-owners or for a holder with a zero holding
6. Holder Integrity
Given deposits and withdrawals happen
When anyone reads Holders for an address
Then it should reflect that holder's deposits minus the Ether withdrawn to them
And only the owner should be able to move Ether or tokens out of the bank

Notes
MinDeposit and Holders are public
Ownership changes require a confirmation step by the new owner
Deposits must be strictly greater than the minimum to be recorded
Ether and token withdrawals are restricted to the owner
