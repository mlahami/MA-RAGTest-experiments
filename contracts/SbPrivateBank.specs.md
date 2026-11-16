User Story: Private Ether Bank With Transfer Log

Title: Deposit at Least the Minimum and Cash Out Any Part of Your Balance

As a bank customer
I want to deposit Ether when the amount reaches the minimum deposit and cash out any part of my balance later
So that I can store Ether safely while every movement is recorded in a transfer log

Acceptance Criteria
1. Deploy the Bank
Given a deployed SbPrivateBankLog contract
When the SbPrivateBank contract is deployed with the log contract address
Then the bank should use that log contract for all records
And MinDeposit should be 1 ETH
2. Deposit Ether
Given the bank is deployed
When I call Deposit with at least MinDeposit
Then my balance in balances should increase by the amount sent
And a "Deposit" message with my address and the amount should be added to the log history
And when I deposit less than MinDeposit, my balance should not change and no message should be logged
3. Receive Plain Ether
Given the bank is deployed
When anyone sends Ether directly to the bank without calling a function
Then the Ether should be accepted without being credited to any balance
4. Cash Out
Given my balance is at least the requested amount
When I call CashOut with an amount
Then that amount should be sent to me
And my balance should decrease by exactly that amount
And a "CashOut" message with my address and the amount should be added to the log
And if the requested amount exceeds my balance, nothing should happen
5. Balance Integrity
Given any sequence of deposits and cash-outs
When I read balances for my address
Then it should always equal my credited deposits minus my cashed-out amounts
And the amount I can obtain in total should be limited to what I have credited
And the Ether credited to other customers should stay available to them
6. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Balances and MinDeposit are public
The log contract must be deployed first and its address provided at deployment
Each customer operates only on their own balance
Deposits below the minimum are kept by the bank without being credited
