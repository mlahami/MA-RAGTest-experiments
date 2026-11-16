User Story: Time-Locked Ether Bank

Title: Deposit Ether With a Time Lock and Collect It After the Lock Expires

As a bank customer
I want to deposit Ether with an unlock time and collect it once that time has passed and my balance is large enough
So that I can save Ether until a chosen moment while every operation is logged

Acceptance Criteria
1. Deploy the Bank
Given a deployed SbUBankLog contract
When the SbUBank contract is deployed with the log contract address
Then the bank should use that log contract for all records
And MinSum should be 2 ETH
2. Deposit With a Lock
Given the bank is deployed
When I call Put with an unlock time and some Ether, or send Ether directly to the bank
Then my account balance should increase by the amount sent
And my unlock time should be set to the given time if it is in the future, otherwise to the current time
And a "Put" message with my address and the amount should be added to the log history
3. Collect After Unlock
Given my balance is at least MinSum and at least the requested amount, and the current time is past my unlock time
When I call Collect with an amount
Then that amount should be sent to me
And my balance should decrease by exactly that amount
And a "Collect" message with my address and the amount should be added to the log
And if my balance is below MinSum or the amount, or the unlock time has not passed, nothing should happen
4. Balance Integrity
Given any sequence of deposits and collections
When I read Acc for my address
Then the balance should always equal my deposits minus my collected amounts
And the total I can obtain should be limited to what I deposited
And the balances of other customers should remain available to them
5. Inspect Accounts
Given deposits have been made
When anyone reads Acc for an address
Then the stored unlock time and balance for that address should be returned
6. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Each account keeps a single balance and a single unlock time
The unlock time can only move forward through later deposits with a later time
MinSum is public and fixed at 2 ETH
Each customer operates only on their own account
