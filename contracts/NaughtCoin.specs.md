User Story: Time-Locked Founder Token

Title: Lock the Founder's Initial Token Supply for Ten Years

As the issuer of the NaughtCoin token
I want the player's entire initial allocation to stay locked for ten years
So that the founder cannot sell or move the supply before the lock expires

Acceptance Criteria
1. Deploy the Token
Given a player address
When NaughtCoin is deployed
Then name should be "NaughtCoin", symbol "0x0" and decimals 18
And INITIAL_SUPPLY should equal 1,000,000 * 10^18 and be minted to the player
And timeLock should equal the deployment timestamp plus 10 * 365 days
And Transfer events from the zero address to the player should be emitted
2. Block Player Transfers During the Lock
Given I am the player and the current time is not after timeLock
When I call transfer(to, amount)
Then the transaction should revert
3. Prevent Any Other Way of Moving Locked Tokens
Given I am the player and the lock is still active
When tokens are moved from my account through approve followed by transferFrom by me or a spender
Then the movement should also be rejected, so the player's balance cannot decrease before timeLock
4. Allow Transfers After the Lock
Given I am the player and the current time is after timeLock
When I call transfer(to, amount)
Then amount should move from me to to
And the call should return true
5. Transfers by Other Holders
Given I am not the player and hold tokens
When I call transfer(to, amount)
Then the transfer should succeed immediately, emit a Transfer event and return true
And it should revert with ERC20InsufficientBalance if my balance is below amount
6. Standard Approvals
Given any holder
When I call approve(spender, amount)
Then allowance(me, spender) should equal amount and an Approval event should be emitted
And transferFrom by a spender with insufficient allowance should revert with ERC20InsufficientAllowance

Notes
The lock applies only to the player address recorded at deployment
Tests can advance time past timeLock with evm_increaseTime to check the post-lock behaviour
There is no owner, minting or burning after deployment
