User Story: Private Ether Cell With Configurable Minimum

Title: Store Ether in a Cell and Collect It Above a Configurable Minimum

As an operator and customer of an Ether storage cell
I want to configure the minimum withdrawable balance and the log contract before locking the setup, then deposit and collect Ether
So that funds can be withdrawn only under clear rules and every operation is logged

Acceptance Criteria
1. Deploy the Cell
Given the SbPrivateEthCell contract is deployed
When the deployment succeeds
Then MinSum should be 0
And no log contract should be configured yet
And the cell should not be marked as initialised
2. Configure the Cell
Given the cell has not been initialised
When anyone calls SetMinSum with a value, or SetLogFile with the address of a deployed SbPrivateEthCellLogFile contract
Then the minimum sum or the log contract should be updated
And after Initialized has been called, both functions should revert
3. Lock the Configuration
Given the configuration is final
When anyone calls Initialized
Then the cell should be marked as initialised permanently
4. Deposit Ether
Given a log contract is configured
When I call Deposit with Ether, or send Ether directly to the cell
Then my balance in balances should increase by the amount sent
And a "Put" message with my address and the amount should be added to the log history
5. Collect Ether
Given my balance is at least MinSum and at least the requested amount
When I call Collect with an amount
Then that amount should be sent to me
And my balance should decrease by exactly that amount
And a "Collect" message with my address and the amount should be added to the log
And if my balance is below MinSum or below the requested amount, nothing should happen
6. Balance Integrity
Given any sequence of deposits and collections
When I read balances for my address
Then it should always equal my deposits minus my collected amounts
And the total I can obtain should be limited to what I deposited
And the balances of other customers should remain available to them
7. Read the Log
Given activity has occurred
When anyone reads History on the log contract with an index
Then the sender, the message text, the value and the timestamp of that record should be returned

Notes
Balances and the minimum sum are public
A log contract must be configured before deposits are logged
Each customer operates only on their own balance
