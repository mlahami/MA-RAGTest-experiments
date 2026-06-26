User Story: Binary Voting System (Yes / No)

Title: Vote on a Single Proposal with Yes or No Options

As a participant in a governance system
I want to vote either “Yes” or “No” on a proposal
So that collective decisions can be made transparently and immutably on-chain

Acceptance Criteria
1. Initialize Proposal
Given a new voting contract is deployed
When a description is provided at deployment
Then a single proposal should be created with:
A description
Yes vote count initialized to 0
No vote count initialized to 0
Voting status set to open
And the deployer should be set as the admin
2. Cast a Vote
Given the voting session is open
When I cast a vote as a user
Then:
If I vote “Yes”, the Yes counter should increase
If I vote “No”, the No counter should increase
My address should be recorded as having voted
I should not be able to vote more than once
And a VoteCast event should be emitted
3. Prevent Double Voting
Given I have already voted
When I try to vote again
Then the transaction should fail
And my vote should not be counted twice
4. Close Voting Session
Given I am the admin
And the voting session is still open
When I close the voting
Then:
The proposal should be marked as closed
No further votes should be accepted
A ProposalClosed event should be emitted with final results
5. Retrieve Voting Results
Given voting is ongoing or completed
When I request results
Then I should receive:
Total “Yes” votes
Total “No” votes
Notes
This contract supports only one proposal at a time
Voting is binary (Yes/No only)
Each address can vote only once
There is no delegation, weighting, or multiple proposals support
The system is suitable for simple governance decisions or polls