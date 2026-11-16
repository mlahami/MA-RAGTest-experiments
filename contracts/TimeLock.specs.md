User Story: Delayed Transaction Execution

Title: Queue Owner Transactions and Execute Them Only Within a Time Window

As the owner of a time-locked account
I want every outgoing call to be queued in advance with a future execution timestamp
So that observers have time to see planned actions before they are executed

Acceptance Criteria
1. Deploy and Fund
Given a deployer
When the TimeLock is deployed
Then the deployer should be recorded as owner
And the contract should accept plain Ether transfers
2. Compute a Transaction Id
Given a target, value, function signature, data and timestamp
When anyone calls getTxId
Then it should return keccak256 of the ABI-encoded parameters
3. Queue a Transaction
Given I am the owner
When I call queue with a timestamp between block.timestamp + MIN_DELAY (10 s) and block.timestamp + MAX_DELAY (1000 s)
Then queued[txId] should become true
And a Queue event should be emitted with txId, target, value, func, data and timestamp
And the call should revert with NotOwnerError if I am not the owner
And it should revert with AlreadyQueuedError if the same transaction is already queued
And it should revert with TimestampNotInRangeError if the timestamp is outside the allowed range
4. Execute a Transaction
Given I am the owner and the transaction is queued
When I call execute with the same parameters at or after its timestamp and no later than timestamp + GRACE_PERIOD (1000 s)
Then queued[txId] should be set to false
And the target should be called with the given value and data, prefixed by the 4-byte selector of func when func is not empty, or with data alone otherwise
And an Execute event should be emitted and the call result returned
And the call should revert with NotQueuedError, TimestampNotPassedError or TimestampExpiredError when applicable
And it should revert with TxFailedError if the target call fails
5. Cancel a Transaction
Given I am the owner and a transaction id is queued
When I call cancel with that id
Then queued[txId] should be set to false
And a Cancel event should be emitted
And it should revert with NotQueuedError if the id is not queued

Notes
Only the owner can queue, execute or cancel; the owner cannot be changed
execute is payable, and the value sent to the target is taken from the contract balance
A transaction is identified only by its parameters, so the same call can be queued again after execution or cancellation
