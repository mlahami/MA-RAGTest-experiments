User Story: Ether Vault With Transfer Log

Title: Deposit Above the Minimum and Cash Out From an Ether Vault

As a vault customer
I want to deposit Ether above the minimum deposit and later cash out any part of my balance
So that I can keep Ether in the vault while every deposit and cash-out is recorded in a log

Acceptance Criteria
1. Deploy the Vault
Given a deployed SbEthVaultLog contract
When the SbEthVault contract is deployed with the log contract address
Then the vault should use that log contract for all records
And MinDeposit should be 1 ETH
2. Deposit Ether
Given the vault is deployed
When I call Deposit with more than MinDeposit
Then my balance in balances should increase by the amount sent
And a "Deposit" message with my address and the amount should be added to the log history
And when I deposit MinDeposit or less, my balance should not change and no message should be logged
3. Receive Plain Ether
Given the vault is deployed
When anyone sends Ether directly to the vault without calling a function
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
And the total I can obtain should be limited to what I have credited
And the Ether credited to other customers should stay available to them
6. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Balances and MinDeposit are public
The log contract must be deployed first and its address provided at deployment
A deposit must be strictly greater than the minimum deposit to be credited
Each customer operates only on their own balance
