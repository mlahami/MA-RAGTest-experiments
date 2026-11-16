User Story: FiftyFlip Coin Game

Title: Place Signed Coin-Flip Bets, Fund a Jackpot and Donate to a Whale Charity

As a coin-flip player
I want to place a signed bet, have part of it donated to a charity (whale) contract and later reveal my ticket
So that I can win 1.9 times my stake or the jackpot while donations reach the charity

Acceptance Criteria
1. Deploy the Game
Given a deployer
When the contract is deployed with whale, bot and secret signer addresses
Then the deployer should become owner
2. Owner Settings
Given I am the owner
When I call setBotAddress or setSecretSigner
Then the bot or signer address should be updated
And other callers should be rejected
3. Place a Bet
Given the balance covers locked bets, jackpot and dev fees
When I call wager with my side, a new ticket id, a last valid block and a signature from the secret signer, paying between 0.01 and 1 ETH
Then 1 percent should fund the jackpot, 2 percent dev fees, 1.9 times the stake be locked
And 2 percent should be sent to the whale's donate function and totalAmountToWhale increased
And the bet should be stored and Wager emitted
And reused or expired tickets, out-of-range amounts, insufficient collateral or invalid signatures should be rejected
4. Reliable Donation
Given the whale contract rejects the donation
When a wager is placed
Then the wager should be reverted
And totalAmountToWhale must only increase when the whale actually received the donation
5. Play a Bet
Given a bet placed in an earlier block less than 250 blocks ago
When I call play with the ticket reveal whose hash is the ticket id
Then a correct side should pay 1.9 times the stake, a jackpot hit adds the jackpot and emits JackpotPayment, and Win or Lose is emitted
And the bet should be closed
And unknown, used or out-of-window tickets should be rejected
6. Refunds and Donations
Given my bet is older than 250 blocks and unsettled
When I call refund
Then my stake should be returned and Refund emitted
And users may add funds with donateForContractHealth and reclaim up to their donation with withdrawDonation
7. Fee Withdrawal
Given I am the owner or the bot
When I call withdrawDevFee or withdrawBotFee with an amount not exceeding dev fees or the balance
Then the amount should be paid and dev fees reduced only if payment succeeded
8. Maintenance and Views
Given the relevant role
When kill, clearStorage or transferAnyERC20Token is called
Then the owner may destroy the contract only with no locked bets, anyone may clear processed bets, and getBetInfo, getContractBalance and getCollateralBalance return their values

Notes
The contract accepts plain Ether transfers
