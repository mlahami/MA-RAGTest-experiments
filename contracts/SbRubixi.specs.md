User Story: Rubixi Multiplier Payout Pyramid

Title: Join an Ether Pyramid That Repays Earlier Participants With a Multiplier

As a participant in an Ether multiplier game
I want to send Ether and be queued for a payout equal to my deposit times the current multiplier
So that I am repaid from later deposits in order of arrival, while the creator collects a bounded fee

Acceptance Criteria
1. Deploy and Creator Role
Given the SbRubixi contract is deployed
When the deployer sets up the contract by calling DynamicPyramid
Then the deployer should become the creator
And if any other address calls DynamicPyramid, the creator must not change
And afterwards the creator can only be replaced through changeOwner called by the current creator
And the initial fee should be 10 percent and the multiplier 300 (3x)
2. Join the Pyramid
Given the contract is active
When I send at least 1 ETH to the contract
Then I should be added to the participant list with a payout of deposit times multiplier / 100
And the fee (halved for deposits of 50 ETH or more) should be added to the collected fees, the rest to the pyramid balance
And while the balance exceeds the payout of the next participant in order, that participant should be paid and the balance reduced
And the multiplier should drop to 200 after the 10th participant and to 150 after the 25th
3. Small Deposits
Given I send less than 1 ETH
When the transfer is received
Then the full amount should be added to the collected fees and I should not be queued
4. Collect Fees
Given I am the creator and collected fees are non-zero
When I call collectAllFees, collectFeesInEther with an amount in whole Ether, or collectPercentOfFees with a percentage up to 100
Then the corresponding amount should be sent to me and deducted from the collected fees
And calls should revert when the collected fees are zero or the percentage exceeds 100
5. Adjust Parameters
Given I am the creator
When I call changeMultiplier with a value between 120 and 300, or changeFeePercentage with a value up to 10
Then the new value should be stored
And out-of-range values should revert
And calls from any other address must have no effect
6. Query Information
Given anyone queries the contract
When they call currentMultiplier, currentFeePercentage, currentPyramidBalanceApproximately, nextPayoutWhenPyramidBalanceTotalsApproximately, feesSeperateFromBalanceApproximately, totalParticipants, numberOfParticipantsWaitingForPayout or participantDetails
Then the corresponding value should be returned, in whole Ether where indicated

Notes
Creator-only functions silently do nothing when called by others, except where a revert is specified
Payouts are made strictly in order of arrival
