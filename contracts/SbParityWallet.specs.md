User Story: Multi-Signature Wallet With Daily Limit

Title: Protect Shared Funds With Multiple Owners, Confirmations and a Daily Spending Limit

As a group of co-owners of a shared Ether wallet
I want small payments to be executed immediately within a daily limit and larger operations to require confirmations from several owners
So that no single person can move large amounts or change the wallet configuration alone

Acceptance Criteria
1. Deploy the Wallet
Given a deployed SbParityWalletLibrary contract that holds the wallet logic
When SbParityWallet is deployed with the library address, a list of additional owners, a required number of confirmations and a daily limit
Then the deployer and every listed address should be owners, with the deployer at position 0 of getOwner
And m_numOwners should equal the number of listed owners plus one
And m_required and m_dailyLimit should equal the given values
And this initial setup must happen exactly once: no later call may re-initialise owners, requirement or limit
2. Deposit Ether
Given the wallet is deployed
When anyone sends Ether to the wallet
Then the funds should be accepted and a Deposit event emitted with sender and amount
3. Execute a Transaction
Given I am an owner
When I call execute with a destination, an amount and empty data, and the amount fits in today's remaining limit, or only one confirmation is required
Then the transfer should be performed immediately and a SingleTransact event emitted
And otherwise the operation should be stored, a confirmation recorded for me and a ConfirmationNeeded event emitted
And calls from non-owners must have no effect
4. Confirm and Revoke
Given a pending operation hash
When enough distinct owners call confirm with that hash
Then the stored transaction should be executed, a MultiTransact event emitted and the operation cleared
And an owner may call revoke before execution to withdraw a confirmation, emitting Revoke
And hasConfirmed should report whether a given owner has confirmed an operation
5. Manage Owners and Settings
Given enough owners confirm the same call
When they call addOwner, removeOwner, changeOwner, changeRequirement, setDailyLimit, resetSpentToday or kill
Then the change should take effect and the corresponding event (OwnerAdded, OwnerRemoved, OwnerChanged, RequirementChanged) be emitted
And a requirement larger than the number of owners must be ignored
6. Query Owners
Given the wallet is configured
When anyone calls getOwner, isOwner, m_numOwners, m_required, m_dailyLimit, m_spentToday or m_lastDay
Then the current values should be returned

Notes
The wallet forwards owner and management calls to the library and runs them on its own storage
The daily spent amount resets automatically on a new day
Only owners can ever change ownership, limits or move funds
