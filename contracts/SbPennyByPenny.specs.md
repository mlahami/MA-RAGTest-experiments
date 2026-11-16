User Story: Time-Locked Savings Bank

Title: Save Ether With a Lock Period and Collect It Once the Lock Expires

As a savings customer
I want to configure the minimum balance and log before locking the setup, deposit Ether with a lock period, and collect once it expires
So that my savings stay locked for a chosen duration while every operation is recorded

Acceptance Criteria
1. Deploy the Bank
Given the SbPennyByPenny contract is deployed
When the deployment succeeds
Then MinSum should be 0
And no log contract should be configured yet
And the bank should not be marked as initialised
2. Configure the Bank
Given the bank has not been initialised
When anyone calls SetMinSum with a value, or SetLogFile with the address of a deployed SbPennyByPennyLogFile contract
Then the minimum sum or the log contract should be updated
And after Initialized has been called, both functions should revert
3. Lock the Configuration
Given the configuration is final
When anyone calls Initialized
Then the bank should be marked as initialised permanently
4. Deposit With a Lock
Given a log contract is configured
When I call Put with a lock duration and some Ether, or send Ether directly to the bank
Then my account balance should increase by the amount sent
And my unlock time should move to the current time plus the lock duration when that is later than the existing unlock time
And a "Put" message with my address and the amount should be added to the log history
5. Collect After Unlock
Given my balance is at least MinSum and at least the requested amount, and the current time is past my unlock time
When I call Collect with an amount
Then that amount should be sent to me
And my balance should decrease by exactly that amount
And a "Collect" message with my address and the amount should be added to the log
And if my balance is below MinSum or the amount, or the unlock time has not passed, nothing should happen
6. Balance Integrity
Given any sequence of deposits and collections
When I read Acc for my address
Then the balance should always equal my deposits minus my collected amounts
And the total I can obtain should be limited to what I deposited
And other customers' balances should remain available to them
7. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Each account keeps a single balance and a single unlock time
The unlock time can only be extended, never shortened
A log contract must be configured before deposits are logged
