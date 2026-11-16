User Story: Statera Deflationary Token

Title: Hold and Transfer a Deflationary ERC20 Token That Burns 1% on Every Transfer

As a holder of the Statera (STA) token
I want to transfer, approve, adjust allowances and burn my tokens
So that every transfer burns a 1% fee and the total supply decreases over time

Acceptance Criteria
1. Initial Supply and Metadata
Given the STA contract is deployed
When the constructor runs
Then name, symbol and decimals should be "Statera", "STA" and 18
And the deployer should receive the whole supply of 100,000,000 tokens (100000000 * 10^18 units)
And totalSupply should equal that amount and a Transfer event from address(0) to the deployer should be emitted
And basePercent should be 100
2. Compute the Burn Fee
Given a value
When I call cut(value)
Then it should return 1% of value after rounding value up to the next multiple of 100
And for example cut(10000) should be 100, cut(150) should be 2 and cut(0) should be 0
3. Transfer with Burn
Given my balance is at least value and the recipient is not address(0)
When I call transfer(to, value)
Then my balance should decrease by value
And the recipient should receive value minus cut(value)
And totalSupply should decrease by cut(value)
And two Transfer events should be emitted: to the recipient for the received amount, and to address(0) for the burned amount
And the call should revert if value exceeds my balance or to is address(0)
4. Approve
Given spender is not address(0)
When I call approve(spender, value)
Then the allowance should be set to value and an Approval event emitted
And approving address(0) should revert
5. Transfer From with Burn
Given from has at least value tokens and has allowed me at least value
When I call transferFrom(from, to, value) with to not address(0)
Then from's balance and my allowance should both decrease by value
And to should receive value minus cut(value) and totalSupply should decrease by cut(value)
And the same two Transfer events as in transfer should be emitted
And the call should revert if the balance or allowance is insufficient, or to is address(0)
6. Adjust Allowances
Given spender is not address(0)
When I call upAllowance or downAllowance with an amount
Then the allowance should increase or decrease by that amount
And an Approval event with the new allowance should be emitted
And decreasing below zero should revert
7. Burn Tokens
Given amount is not zero and does not exceed the account balance
When I call destroy(amount), or destroyFrom(account, amount) with sufficient allowance
Then the balance and totalSupply should decrease by amount and a Transfer event to address(0) should be emitted
And destroyFrom should also reduce my allowance from account by amount
And zero amounts, insufficient balances or insufficient allowances should revert
Notes
SafeMath and ERC20Detailed are internal building blocks in the same file; tests interact only with STA
Recipients always receive less than the amount sent, except when the fee rounds to 0
None of the require checks have revert messages
