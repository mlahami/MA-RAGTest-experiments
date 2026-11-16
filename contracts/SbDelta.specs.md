User Story: Delta Token Sale Desk

Title: Buy Delta Tokens with Ether and Share Proceeds with a Partner

As a token buyer
I want to send Ether and receive Delta tokens from the owner's token allowance at a fixed price
So that I can acquire tokens while the sale proceeds are split between the owner and a partner

Acceptance Criteria
1. Deploy the Sale
Given a deployer
When the contract is deployed with a token contract address and a partner (owner2) address
Then the deployer should become owner
And the token address, owner2, active flag set to 1 and a token price of 0.001 ETH should be stored
2. Buy Tokens
Given the sale is active
When I call tokens_buy, or send plain Ether, with at least the token price
Then the number of tokens should be computed as value multiplied by 10^18 divided by the token price
And the sale should call transferFrom on the token contract moving that amount from the owner to me
And if the token transfer fails the function should return false without paying the partner
And 30 percent of my payment should be sent to owner2
And the function should return true
3. Reject Invalid Purchases
Given the sale is inactive, or I send less than the token price
When I try to buy
Then the transaction should be reverted
4. Partner Share Is Guaranteed
Given a purchase succeeds
When the 30 percent share cannot be delivered to owner2
Then the whole purchase should be reverted
And the purchase must never report success while owner2 has not received its share
5. Withdraw Proceeds
Given I am the owner
When I call withdraw with an amount
Then that amount, or the whole balance when the amount is zero, should be sent to me
And if the payment to me fails the withdrawal should revert rather than return true
And a non-owner should be rejected
6. Change Price
Given I am the owner
When I call change_token_price with a new price
Then the token price should be updated and true returned
And a non-owner should be rejected
7. Activate or Pause
Given I am the owner
When I call change_active with a value
Then active should be updated, with zero pausing purchases
And a non-owner should be rejected

Notes
The owner must have approved this contract on the token for sales to deliver tokens
The remaining 70 percent of every payment stays in the contract until withdrawn
All state variables are publicly readable
Return values of true must always mean the Ether movement actually happened
