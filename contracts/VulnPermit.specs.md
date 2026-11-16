User Story: Token Vault with Permit Deposits

Title: Deposit Tokens Directly or with a Signed Permit and Withdraw Them

As a token holder
I want to deposit tokens into the VulnPermit vault either with a prior approval or with a signed permit
So that I can move my tokens into the vault, and no one can deposit tokens from my account without my authorization

Acceptance Criteria
1. Configure the Vault Token
Given the vault is deployed with an ERC20 token address
When I query token
Then it should return that token address
2. Deposit with Approval
Given I have approved the vault for at least amount tokens and hold that amount
When I call deposit(amount)
Then amount tokens should be transferred from me to the vault
And if the transfer fails, the transaction should revert ("Transfer failed" when the token returns false)
3. Deposit with a Valid Permit
Given the token supports permit and target has signed a valid permit (v, r, s) authorizing the vault for amount
When anyone calls depositWithPermit(target, amount, v, r, s)
Then the permit should be applied on the token
And amount tokens should be transferred from target to the vault
4. Require Authorization from the Target
Given target has not signed a valid permit for the vault
When depositWithPermit is called for target
Then the deposit should be rejected with "Permit failed"
And no tokens should be moved from target
And when the token does not support permit, depositWithPermit should also revert with "Permit failed"
5. Withdraw Tokens
Given the vault holds at least amount tokens
When I call withdraw(amount)
Then amount tokens should be transferred from the vault to me
And if the vault cannot pay, the transaction should revert
Notes
VulnPermitMockToken is a helper ERC20 in the same file (configurable decimals, public mint, no permit support); tests deploy it as the vault token and mint balances
The vault does not keep per-user deposit records and emits no events of its own
Token Transfer events come from the token contract
