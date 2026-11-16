User Story: Owner-Controlled Ether Multiplier Vault

Title: Hold Ether, Let the Owner Withdraw or Execute Calls, and Offer a Balance Multiplication

As the owner of a small Ether vault
I want to receive Ether, withdraw it, and execute arbitrary calls from the vault while attaching Ether
So that I can manage the vault's funds and interact with other contracts on its behalf

Acceptance Criteria
1. Deploy the Vault
Given a deployer account
When the contract is deployed
Then the deployer should be recorded as Owner
And Owner should be readable publicly
2. Receive Ether
Given any account
When it sends plain Ether to the contract
Then the transfer should be accepted
And the contract balance should increase by the amount sent
3. Withdraw All Funds
Given I am the Owner
When I call withdraw
Then the full contract balance should be transferred to me
And the contract balance should become zero
And any non-owner calling withdraw should be rejected
4. Execute a Call as the Owner
Given I am the Owner
When I call Command with a target address, call data and an attached Ether amount
Then the target should be called with the given data
And exactly the attached Ether should be forwarded to the target
And any non-owner calling Command should be rejected
5. Failed Command Is Reverted
Given I am the Owner
When the target of Command reverts or otherwise fails
Then the whole Command transaction should be reverted
And the attached Ether should not remain in the vault
And the vault balance should be unchanged after the failed attempt
6. Multiply
Given any account
When it calls multiplicate with a recipient address and sends Ether at least equal to the contract balance
Then the contract should attempt to transfer the balance plus the sent amount to the recipient
And if the sent value is lower than the contract balance, nothing should be paid out and the Ether should stay in the contract
And if the payout cannot be covered the transaction should be reverted

Notes
Only the Owner may withdraw funds or execute calls
The Owner is fixed at deployment; there is no ownership transfer function
Command is intended for owner-driven interactions such as paying or calling other contracts
Callers of Command should be able to rely on the call having succeeded whenever the transaction succeeds
The contract keeps no per-user accounting; all Ether is pooled
