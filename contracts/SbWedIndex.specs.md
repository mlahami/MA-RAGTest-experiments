User Story: Wedding Contract Index

Title: Maintain a Public Index of Wedding Contracts with an Owner-Managed Admin Account

As the operator of a wedding registry service
I want anyone to append entries describing deployed wedding contracts, while I keep a two-step ownership and an emergency execute facility
So that a front-end can list all wedding contracts and I can safely manage the index contract

Acceptance Criteria
1. Deploy the Index
Given a deployer account
When the contract is deployed
Then the deployer should be recorded as owner
And newOwner should be the zero address
And the index should be empty
2. Propose a New Owner
Given I am the owner
When I call changeOwner with a new address
Then newOwner should be set to that address
And the current owner should remain unchanged until acceptance
And a non-owner calling changeOwner should be rejected
3. Accept Ownership
Given an address has been proposed as newOwner
When that address calls acceptOwnership
Then it should become the owner
And when any other address calls acceptOwnership, ownership should not change
4. Execute a Call as the Owner
Given I am the owner
When I call execute with a destination, an Ether value and call data
Then the destination should be called with the data and receive the specified value from the contract balance
And a non-owner calling execute should be rejected
5. Failed Execution Is Reverted
Given I am the owner
When the destination of execute reverts, or the contract cannot provide the value
Then the execute transaction should be reverted
And no state or balance change should remain
6. Write an Index Entry
Given any user
When they call writeIndex with a wedding contract address string, partner names, wedding date and a display flag
Then a new entry should be appended to the index
And the entry's index date should be the current block timestamp, ignoring the supplied index date
And an IndexWritten event should be emitted with the timestamp and the supplied values
7. Read the Index
Given entries exist
When a user calls numberOfIndex or reads indexarray at a position
Then the number of entries and the stored entry fields should be returned

Notes
Anyone can write index entries; there is no moderation or deletion
The execute facility is an owner-only safety tool behaving like a one-of-one multisig, whose success the owner can rely on
The contract has no receive function, so it cannot accept plain Ether transfers
