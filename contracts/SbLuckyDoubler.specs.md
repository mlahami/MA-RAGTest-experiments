User Story: Lucky Doubler Deposit Game With Random Payout Order

Title: Deposit 1 ETH and Be Repaid With a Multiplier in a Random Order

As a participant
I want to deposit exactly 1 ETH and have my entry paid out at the current multiplier when the balance allows
So that I can earn a return, with the next entry to be paid chosen at random among unpaid entries

Acceptance Criteria
1. Deploy the Game
Given the SbLuckyDoubler contract is deployed
When the deployment succeeds
Then the deployer should be the owner
And the fee should be 5 percent and the multiplier 125 (1.25x)
2. Join With a Deposit
Given I send Ether directly to the contract
When the amount is at least 1 ETH
Then exactly 1 ETH should be used as my deposit and any excess returned to me
And a new entry should be recorded with payout = 1 ETH times multiplier / 100
And my user statistics should show one more deposit
And the deposit minus the fee should be added to the payout balance
And amounts below 1 ETH should be returned to me without creating an entry
3. Pay a Random Entry
Given there are unpaid entries
When a new deposit is processed
Then one unpaid entry should be selected at random in a way no participant can predict or influence
And if the payout balance exceeds that entry's payout, the entry should be paid, marked as paid and removed from the unpaid list
And the paid user's payout counter should increase
And any Ether held beyond the payout balance should be sent to the owner as fees
4. Owner Settings
Given I am the owner
When I call changeOwner, changeMultiplier with a value between 110 and 150, or changeFee with a value up to 5
Then the new value should be stored
And a multiplier outside 110 to 150 or a fee above 5 should revert
And calls from other addresses should have no effect
5. Query Information
Given anyone queries the contract
When they call multiplierFactor, currentFee, totalEntries, userStats or entryDetails
Then the multiplier, the fee, the number of entries, a user's deposits and payouts, or an entry's address, payout in finney and paid status should be returned with a description text
And unknown users or out-of-range entries should return empty values

Notes
Every entry is fixed at 1 ETH regardless of the amount sent
Payout order is random rather than first-come first-served
The fee percentage can never exceed 5
