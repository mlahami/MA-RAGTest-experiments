User Story: King of the Ether Throne

Title: Pay the Current Claim Price to Become Monarch and Compensate the Previous One

As a player of a chain game
I want to pay the current claim price to take the throne, have the previous monarch compensated, and have any overpayment refunded
So that the throne passes fairly from one paying monarch to the next

Acceptance Criteria
1. Deploy the Throne
Given a deployer
When the contract is deployed
Then the deployer should become the wizard
And the claim price should be 0.1 ETH
And the current monarch should be the wizard named "[Vacant]" with a claim price of zero
2. Claim the Throne
Given the current claim price
When I call claimThrone with my name, or send Ether with my name as transaction data, paying at least the claim price
Then the previous monarch should be appended to the past monarchs list
And I should become the current monarch with my name, the price paid and the current timestamp
And a ThroneClaimed event should be emitted with my address, name and the new claim price
3. Underpayment
Given I pay less than the claim price
When I try to claim
Then the claim should be rejected and my payment returned to me
And if my payment cannot be returned the transaction should be reverted
4. Overpayment
Given I pay more than the claim price
When my claim is processed
Then the excess should be refunded to me and only the claim price kept
And if the refund cannot be delivered the claim should be reverted
5. Compensation
Given the current monarch is not the wizard
When a claim succeeds
Then the previous monarch should receive the claim price minus a 1 percent wizard commission
And if this compensation cannot be delivered the claim should be reverted
And when the throne was vacant the whole payment should remain as wizard commission
6. Price Increase
Given a successful claim
When the new price is calculated
Then it should be 1.5 times the previous price, rounded down to a precision step that depends on its size
7. Wizard Functions
Given I am the wizard
When I call sweepCommission with an amount
Then that amount should be sent to me, reverting if the payment fails
And when I call transferOwnership the new address should become wizard
And calls by others should have no effect
8. Queries
Given any user
When they call numberOfMonarchs, currentClaimPrice, currentMonarch or pastMonarchs
Then the stored values should be returned

Notes
Monarch compensation and refunds must never be silently lost
