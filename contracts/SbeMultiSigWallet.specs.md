User Story: Multi-Owner Ether Wallet

Title: Submit, Confirm and Execute Wallet Transactions with a Required Number of Owner Approvals

As one of the owners of a shared wallet
I want transactions to be proposed, confirmed by several owners and executed only once enough confirmations are collected
So that no single owner can move the wallet's funds or call external contracts alone

Acceptance Criteria
1. Create the Wallet
Given a list of owner addresses and a required number of confirmations
When the wallet is deployed
Then each owner should be stored in owners and flagged in isOwner
And numConfirmationsRequired should be set
And deployment should revert with "owners required" if the list is empty
And it should revert with "invalid number of required confirmations" if the number is 0 or greater than the number of owners
And it should revert with "invalid owner" for the zero address and "owner not unique" for a duplicate owner
2. Receive Ether
Given anyone holds Ether
When they send Ether directly to the wallet
Then the Ether should be accepted
And a Deposit event should be emitted with the sender, the amount and the new wallet balance
3. Submit a Transaction
Given I am an owner
When I call submitTransaction with a destination, a value and call data
Then a new transaction should be appended with executed false and 0 confirmations
And a SubmitTransaction event should be emitted with my address, the transaction index, destination, value and data
And a non-owner caller should be rejected with "not owner"
4. Confirm a Transaction
Given I am an owner and the transaction exists and is not executed
When I call confirmTransaction
Then its confirmation count should increase by 1 and isConfirmed should be true for me
And a ConfirmTransaction event should be emitted
And the call should revert with "tx does not exist", "tx already executed" or "tx already confirmed" when applicable
5. Revoke a Confirmation
Given I am an owner who confirmed an existing, non-executed transaction
When I call revokeConfirmation
Then its confirmation count should decrease by 1 and isConfirmed should be false for me
And a RevokeConfirmation event should be emitted
And the call should revert with "tx not confirmed" if I had not confirmed it
6. Execute a Transaction
Given I am an owner and the transaction exists, is not executed and has at least numConfirmationsRequired confirmations
When I call executeTransaction
Then the transaction should be marked executed
And the value and data should be sent to the destination
And an ExecuteTransaction event should be emitted
And the call should revert with "cannot execute tx" if confirmations are insufficient
And it should revert with "tx failed" if the destination call fails, leaving the transaction not executed
7. Query the Wallet
Given the wallet is deployed
When I call getOwners, getTransactionCount or getTransaction
Then I should receive the owner list, the number of transactions, or the stored fields of the given transaction

Notes
The set of owners and the required number of confirmations are fixed at deployment
Any owner may execute a sufficiently confirmed transaction, not only the submitter
Transactions are identified by their index in submission order, starting at 0
No events are emitted for failed operations
