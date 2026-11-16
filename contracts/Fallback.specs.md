User Story: Contribution-Based Ownership Fund

Title: Collect Small Contributions and Grant Ownership to the Largest or Paying Contributor

As a supporter of a community fund
I want to make small contributions that are recorded per address
So that the leading contributor becomes the owner who can withdraw the fund

Acceptance Criteria
1. Deploy the Fund
Given a deployer
When Fallback is deployed
Then the deployer should be the owner
And the deployer's contribution should be recorded as 1000 ETH
2. Contribute
Given any account
When it calls contribute sending less than 0.001 ETH
Then its contribution should increase by the amount sent
And the call should revert if 0.001 ETH or more is sent
3. Become Owner by Contribution
Given my total contribution exceeds the current owner's contribution
When my contribute call completes
Then I should become the owner
4. Read My Contribution
Given any account
When it calls getContribution
Then it should receive its own recorded contribution
And contributions(address) should return the recorded contribution of any address
5. Direct Payments
Given I already have a non-zero contribution
When I send a non-zero amount of Ether directly to the contract
Then the payment should be accepted
And I should become the owner
And the payment should be rejected if I have no contribution or send 0 Ether
6. Withdraw the Fund
Given I am the owner
When I call withdraw
Then the entire contract balance should be transferred to me
And a non-owner caller should be rejected with "caller is not the owner"

Notes
contribute and the direct-payment path revert without a reason string
Direct payments are not added to the sender's recorded contribution
Contributions are never reduced, even after a withdrawal
No events are emitted
