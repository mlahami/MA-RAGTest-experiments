User Story: Batch Token Distribution

Title: Load a List of Token Transfers and Distribute Them in Gas-Bounded Batches

As the operator of a token airdrop
I want to load packed transfer entries and then execute them in one or more runs
So that many recipients receive their tokens without exceeding block gas limits

Acceptance Criteria
1. Deploy the Distributor
Given a deployed token contract implementing transfer and balanceOf
When the distributor is deployed with that token address
Then the deployer should become owner
And the token address should be stored and readable
And next and totalToDistribute should be zero
2. Load Transfers
Given I am the owner and distribution has not started
When I call fill with an array of packed numbers, each holding an amount in the upper bits and a recipient address in the lower 160 bits
Then each entry should be decoded and appended to the transfer list
And totalToDistribute should increase by the sum of the amounts
And fill after distribution has started should be reverted
And calls from other accounts should have no effect
3. Run the Distribution
Given I am the owner and transfers are loaded
When I call run for the first time
Then the call should revert unless the distributor's token balance equals totalToDistribute
And transfers should be executed in order while enough gas remains
And next should record how many transfers have been processed
And any failed token transfer should revert the run
And further calls to run should continue from where the previous run stopped
4. Progress Queries
Given transfers have been loaded
When hasTerminated or nTransfers is called
Then nTransfers should return the number of loaded entries
And hasTerminated should be true only when entries exist and all have been processed
5. Change Owner
Given I am the owner
When I call changeOwner with a new address
Then the new address should become owner
And calls from other accounts should have no effect
6. Owner Execute
Given I am the owner
When I call execute with a destination, an Ether value and call data
Then the destination should be called with that data and value
And if that call fails the execute transaction should be reverted
And calls from other accounts should have no effect

Notes
The file includes a simple token contract that mints an initial supply to its deployer and can be used as the distributed token
Owner-restricted functions silently do nothing for other callers
Entries with a zero amount are skipped
