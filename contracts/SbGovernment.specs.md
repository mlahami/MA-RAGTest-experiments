User Story: Government Credit Scheme

Title: Lend Money to the Government and Be Repaid With Interest

As a creditor
I want to lend at least 1 ETH to the government and be repaid 110 percent in order of arrival
So that I earn interest while the system keeps running, and the last creditor wins the reserve if the system stops receiving credit

Acceptance Criteria
1. Establish the Government
Given the SbGovernment contract is deployed with an optional Ether amount
When the deployment succeeds
Then the deployer should be the corruptElite
And the Ether sent should become profitFromCrash
And lastTimeOfNewCredit should be the deployment time and round should be 0
2. Lend Money
Given the last credit was less than 12 hours ago
When I call lendGovernmentMoney with a buddy address and at least 1 ETH, or send Ether directly
Then I should be added to creditorAddresses with an amount of 110 percent of my loan in creditorAmounts
And lastTimeOfNewCredit should be updated
And 5 percent should be sent to the corruptElite and 5 percent added to profitFromCrash while it is below 10000 ETH
And if my buddy has credited at least my amount, my buddy should receive 5 percent
And if the balance minus profitFromCrash covers the next unpaid creditor, that creditor should be paid and lastCreditorPayedOut increased
And the call should return true
3. Too Small Loan
Given the system is alive
When I lend less than 1 ETH
Then my Ether should be returned and the call should return false
4. System Crash
Given 12 hours have passed without new credit
When anyone calls lendGovernmentMoney
Then their Ether should be returned, the last creditor should receive profitFromCrash and the corruptElite the remaining balance
And the creditor lists should be emptied, profitFromCrash and lastCreditorPayedOut reset to 0, round increased and the call return false
And this reset must always complete regardless of how many creditors were registered
5. Other Functions
Given the system is running
When anyone calls investInTheSystem with Ether, it should be added to profitFromCrash
And the corruptElite can call inheritToNextGeneration to hand over the role; others have no effect
And totalDebt, totalPayedOut, getCreditorAddresses and getCreditorAmounts should return the outstanding debt, the amount repaid and the creditor lists

Notes
Creditors are repaid strictly in the order they lent
The scheme must remain operable for every round, no matter how large it grows
