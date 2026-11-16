User Story: Time-Locked Token Bank

Title: Lock ERC20 Tokens Until a Chosen Time and Unlock Them Afterwards

As a token holder
I want to lock an amount of an ERC20 token in the VulnerableBank until a future time
So that my tokens stay in the bank for the whole lock period and are returned to me once it has elapsed

Acceptance Criteria
1. Create a Locker
Given I hold at least amount of an ERC20 token and have approved the bank for that amount
When I call createLocker(tokenAddress, amount, lockTime) with lockTime in the future
Then amount tokens should be transferred from me to the bank
And a new locker should be recorded under my address with the amount, lock time and token address
And the locker should be marked as holding locked tokens
And the locker id should be the next value of a global counter starting at 1 and increasing by 1 for each locker created
2. Validate Locker Creation
Given I call createLocker
When amount is 0
Then the transaction should revert with "Amount must be greater than 0"
And when lockTime is not later than the current block timestamp, it should revert with "Lock time must be in the future"
And when my token balance is lower than amount, it should revert with "Insufficient token balance"
3. Unlock After the Lock Period
Given I own a locker whose lock time has passed
When I call unlockToken(lockerId)
Then the locked amount should be transferred back to me
And the locker amount should be reset to 0
4. Keep Tokens Locked During the Lock Period
Given I own a locker whose lock time has not yet passed
When I call unlockToken(lockerId)
Then the request should be rejected
And no tokens should leave the bank
5. Prevent Double Unlocking
Given I have already unlocked a locker
When I call unlockToken again with the same lockerId
Then no further tokens should be released to me
6. Reject Unknown Lockers
Given I do not own a locker with the given id
When I call unlockToken(lockerId)
Then the transaction should revert with "No locked tokens"
Notes
Lockers are private and stored per owner; there is no public getter, so effects are observed through token balances
Each locker can hold one ERC20 token; the test environment provides VulnerableBankMockToken (constructor name and symbol, mintable by anyone) as the token to lock
No events are emitted
