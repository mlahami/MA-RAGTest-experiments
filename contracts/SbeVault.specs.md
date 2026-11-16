User Story: Token Vault with Shares

Title: Deposit ERC20 Tokens into a Vault and Withdraw Them Through Proportional Shares

As a token holder
I want to deposit tokens into a shared vault and receive shares representing my portion
So that I can later redeem my shares for my proportional part of the vault balance, including any tokens added to it

Acceptance Criteria
1. Deploy the Vault
Given an ERC20 token address
When SbeVault is deployed with the token
Then token should return that address
And totalSupply should be zero
2. First Deposit
Given the vault has no shares and I approved the vault
When I call deposit with an amount
Then I should receive shares equal to the amount
And balanceOf for me and totalSupply should increase by that amount
And the amount should be transferred from me to the vault
3. Subsequent Deposits
Given the vault already has shares
When I call deposit with an amount
Then I should receive amount * totalSupply / vault token balance shares
And balanceOf for me and totalSupply should increase by those shares
And the amount should be transferred from me to the vault
And the deposit should fail if the token transfer fails (for example missing approval or insufficient balance)
4. Withdraw
Given I hold shares
When I call withdraw with a number of shares
Then I should receive shares * vault token balance / totalSupply tokens
And my balanceOf and totalSupply should decrease by the shares
And the transaction should fail if I try to burn more shares than I own
5. Share Value Growth
Given tokens are transferred directly to the vault without a deposit
When a shareholder withdraws
Then the extra tokens are distributed to shareholders in proportion to their shares

Notes
Shares are internal accounting values, not a transferable ERC20 token
The contract has no owner and emits no events
The test environment provides SbeVaultMockToken (constructor name, symbol, decimals; mintable by anyone) to deploy the token passed to the SbeVault constructor
