User Story: On-Chain Marriage Record

Title: Record a Marriage, Its Major Events and Guest Messages with an Owner-Managed Contract

As a married couple
I want to register our marriage, record major life events and receive messages and Ether gifts from guests
So that our marriage history is publicly preserved and gifts reach us

Acceptance Criteria
1. Deploy the Contract
Given a deployer
When the contract is deployed with an owner address
Then that address should be the owner
And no events or messages should exist
2. Create the Marriage
Given I am the owner and no major events exist
When I call createMarriage with both partner names, vows and a URL
Then the partners, vows and current timestamp as marriage date should be stored
And the status should become "Married"
And a "Marriage" major event should be recorded and a MajorEvent event emitted
And a second call, or a call by a non-owner, should be rejected
3. Change Status
Given I am the owner and the status is "Married"
When I call setStatus with a new status and URL
Then the status should be updated and a "Changed Status" major event should be recorded
And a non-owner should be rejected
4. Add a Major Event
Given I am the owner and the status is "Married"
When I call setMajorEvent with a name, description and URL
Then the event should be appended with the current timestamp and MajorEvent emitted
And the call should be rejected if the status is not "Married" or the caller is not the owner
5. Send a Message
Given the status is "Married"
When any user calls sendMessage with a name, text, URL and optional Ether
Then the message and its value should be stored and MessageSent emitted
And if Ether was attached the contract balance should be transferred to the owner
And sending a message while not married should be rejected
6. Ownership Management
Given I am the owner
When I call changeOwner with a new address and that address calls acceptOwnership
Then ownership should move to the new address
And acceptOwnership from any other address should have no effect
7. Owner Execute
Given I am the owner
When I call execute with a destination, value and data
Then the destination should be called with the data and value
And if the call fails the whole transaction should be reverted with no state change
And a non-owner should be rejected
8. Counts
Given events and messages exist
When numberOfMajorEvents or numberOfMessages is called
Then the correct counts should be returned

Notes
Status comparison is an exact string match against "Married"
Gifts are forwarded to the owner immediately
