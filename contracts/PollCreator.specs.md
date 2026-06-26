User Story: Dynamic On-Chain Polling System

Title: Create and Participate in Decentralized Polls

As a platform admin or user
I want to create polls and vote on predefined options
So that community decisions can be collected transparently and immutably on-chain

Acceptance Criteria
1. Create a Poll (Admin Only)
Given I am the admin
When I create a poll with a question and at least two options
Then a new poll should be stored on-chain with:
A unique poll ID
The question text
A list of voting options
A vote counter initialized for each option
Status set to open
And a PollCreated event should be emitted
2. Vote on a Poll
Given a poll exists and is open
When I cast a vote for a valid option
Then:
My vote should be recorded
The selected option’s vote count should increase
I should not be able to vote more than once per poll
And a VoteRegistered event should be emitted
3. Prevent Invalid Voting
Given a poll does not exist or is closed
When I attempt to vote
Then the transaction should fail
And if I already voted, the transaction should be rejected
And if the option index is invalid, the transaction should fail
4. Retrieve Poll Results
Given a poll exists
When I request poll results
Then I should receive:
The poll question
The list of options
The vote count for each option
5. Close a Poll (Admin Only)
Given I am the admin
When I close a poll
Then the poll should be marked as closed
And no further votes should be accepted
Notes
Each poll tracks votes per option using an array
Voting is one-time per address per poll
Only the admin can create and close polls
Polls are immutable once created except for vote counts and open/close status
There is no delegation or weighted voting mechanism