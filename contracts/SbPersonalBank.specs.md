User Story: Personal Ether Bank With Activity Log

Title: Deposit Ether and Collect It Once a Minimum Balance Is Reached

As a bank customer
I want to deposit Ether into my personal account and withdraw it once my balance reaches the minimum sum
So that my savings are kept safe and every deposit and withdrawal is recorded in a log

Acceptance Criteria
1. Deploy the Bank
Given the SbPersonalBank contract is deployed
When the deployment succeeds
Then MinSum should be 1 ETH
And a new SbPersonalBankLogFile log contract should be created and used for records
And the bank should not yet be marked as initialised
2. Configure Before Initialisation
Given the bank has not been initialised
When anyone calls SetMinSum with a value or SetLogFile with a log contract address
Then the minimum sum or the log contract should be updated
And once Initialized has been called, both functions should revert
3. Lock the Configuration
Given the configuration is final
When anyone calls Initialized
Then the bank should be marked as initialised permanently
4. Deposit Ether
Given the bank is deployed
When I call Deposit with Ether, or send Ether directly to the bank
Then my balance in balances should increase by the amount sent
And a "Put" message with my address and the amount should be added to the log history
5. Collect Ether
Given my balance is at least MinSum and at least the requested amount
When I call Collect with an amount
Then that amount should be sent to me
And my balance should decrease by exactly that amount
And a "Collect" message with my address and the amount should be added to the log
And if the payment fails, my balance must remain unchanged
And if my balance is below MinSum or below the requested amount, nothing should happen
6. Balance Integrity
Given any sequence of deposits and collections
When I read balances for my address
Then it must always equal my total deposits minus my total collected amounts
And I must never be able to collect more Ether than I deposited
7. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Balances are public; the minimum sum is public
The log contract records every successful deposit and collection
Each customer can only withdraw from their own balance
