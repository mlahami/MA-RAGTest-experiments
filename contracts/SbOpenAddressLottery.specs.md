User Story: Open Address Lottery

Title: Win Seven Times Your Ticket When Your Address Is Lucky

As a lottery participant
I want to buy a ticket of at least 0.1 ETH and win seven times its price when my address maps to the lucky number
So that I have a one-in-eight chance to win a jackpot, at most once per address

Acceptance Criteria
1. Deploy the Lottery
Given the SbOpenAddressLottery contract is deployed
When the deployment succeeds
Then the deployer should be the owner
And the lucky number should be 7
And a secret seed should be initialised and the reseed block recorded
2. Participate
Given I have not won before
When I call participate with at least 0.1 ETH, or send at least 0.1 ETH directly while not being the owner
Then my lucky number should be computed from my address and the secret seed
And if it equals 7, I should be marked as a winner and receive seven times my ticket, or the whole balance if it is smaller
And if more than 1000 blocks passed since the last reseed, the seed should be refreshed
And a ticket below 0.1 ETH should be accepted without effect
And the transaction should revert if I have already won
3. Lucky Number Query
Given any address
When anyone calls luckyNumberOfAddress
Then a number between 0 and 7 derived from that address and the current seed should be returned
4. Owner Funding
Given I am the owner
When I send Ether directly to the contract
Then the Ether should be added to the jackpot without counting as a ticket
5. Manual Reseed
Given I am the owner
When I call forceReseed
Then only the secret seed and the reseed block should change
And the owner and the lucky number 7 must remain unchanged
And calls from other addresses should revert
6. Close the Lottery
Given I am the owner
When I call kill
Then the contract should be closed and its balance sent to me
And calls from other addresses should revert

Notes
Every address can win at most once
The chance of winning is one in eight for every participant
The secret seed and the reseed block are private
The lucky number is not changeable by anyone
