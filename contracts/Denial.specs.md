User Story: Shared Withdrawal Fund

Title: Split Periodic 1% Withdrawals Between a Withdrawal Partner and the Fixed Owner

As a withdrawal partner of a pooled fund
I want each withdrawal to pay 1% of the fund to me and 1% to the owner
So that both of us receive a share of the pooled Ether over time

Acceptance Criteria
1. Fund the Contract
Given anyone holds Ether
When they send Ether directly to Denial
Then the Ether should be accepted
And contractBalance should return the new balance
2. Set the Withdrawal Partner
Given any account
When it calls setWithdrawPartner with an address
Then partner should be set to that address
3. Withdraw
Given the contract holds a balance B
When anyone calls withdraw
Then the partner should be sent B / 100 wei
And the owner address 0xA9E should be sent B / 100 wei
And the contract balance should decrease by up to 2 * (B / 100)
And the last withdrawal time and the partner's cumulative withdrawn amount should be updated internally
4. Partner Payment Result
Given the partner is set
When withdraw is called and the partner payment does not succeed
Then the withdrawal should still proceed and pay the owner
5. Owner Payment Failure
Given the owner payment cannot be completed
When withdraw is called
Then the whole call should revert
6. Small Balances
Given the balance is below 100 wei
When withdraw is called
Then both payments should be 0 wei and the call should succeed
7. Check the Balance
Given the contract is deployed
When anyone calls contractBalance
Then it should return the contract's Ether balance

Notes
owner is a constant address (0xA9E), not the deployer
setWithdrawPartner and withdraw have no access control and no rate limit
timeLastWithdrawn and withdrawPartnerBalances are internal and have no getter
If no partner has been set, the partner share is sent to the zero address
