User Story: Personal Blockchain Address Book

Title: Manage Personal Contacts on Blockchain

As a blockchain user
I want to store, retrieve, and manage my personal contacts using names mapped to wallet addresses
So that I can easily reference and use addresses without remembering or copying long hexadecimal values

Acceptance Criteria
1. Add or Update a Contact
Given I am a user with a wallet address
When I add a contact with a unique name and a blockchain address
Then the contact should be stored under my account
And if the contact name already exists, it should update the existing contact
And an event should be emitted confirming the addition or update
2. Retrieve a Contact Address
Given I have previously stored a contact
When I request the address using the contact’s name
Then I should receive the correct blockchain address
And if the contact does not exist, the transaction should fail
3. List All Contact Names
Given I have added multiple contacts
When I request the list of all my contacts
Then I should receive an array of all stored contact names
4. Remove a Contact
Given I have an existing contact
When I remove the contact using its name
Then the contact should be deleted from my address book
And an event should be emitted confirming the removal
And if the contact does not exist, the transaction should fail
Notes
Each user manages their own independent address book
Contact names act as unique identifiers per user
Only the owner of the address book can access and modify their contacts
Removing a contact does not clean up the name list array, which may result in stale entries