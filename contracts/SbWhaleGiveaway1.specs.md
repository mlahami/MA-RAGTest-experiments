User Story: Owner-Managed Giveaway Wallet

Title: Collect Ether, Pay Out the Pool on Qualifying Contributions, and Let the Owner Manage Funds

As the owner of a giveaway wallet
I want the wallet to accept Ether, release its pool when a contribution larger than 1 ETH arrives, and let me withdraw funds or execute calls
So that I can run a simple promotional pool and manage it from one address

Acceptance Criteria
1. Deploy the Wallet
Given a deployer account
When the contract is deployed
Then the deployer should be recorded as Owner
And Owner should be publicly readable
2. Receive Ether
Given any account
When it sends plain Ether to the contract
Then the transfer should be accepted and the balance should increase
3. Claim the Freebie
Given the wallet holds Ether
When a caller invokes GetFreebie sending strictly more than 1 ETH
Then the contract should transfer its whole balance to the Owner first
And then transfer whatever balance remains to the caller
And when 1 ETH or less is sent, no payout should occur and the Ether should stay in the wallet
4. Withdraw Funds
Given I am the Owner
When I call withdraw
Then the entire contract balance should be transferred to me
And a caller that is not the Owner should be rejected
And a designated recovery address should become Owner when it calls withdraw
5. Execute a Call as the Owner
Given I am the Owner
When I call Command with a target address, call data and attached Ether
Then the target should be called with that data and the attached Ether should be forwarded
And any non-owner calling Command should be rejected
6. Failed Command Is Reverted
Given I am the Owner
When the target of Command reverts or fails
Then the whole transaction should be reverted
And the attached Ether should be returned to me rather than retained by the wallet
And the wallet balance should be the same as before the call

Notes
All payouts use full-balance transfers; there is no per-user accounting
Only the Owner may withdraw or execute calls
The Owner can only change through the recovery address path in withdraw
Command is intended for owner-driven payments and contract interactions whose success the Owner can rely on
