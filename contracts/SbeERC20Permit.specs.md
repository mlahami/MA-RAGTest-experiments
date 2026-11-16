User Story: Token with Signed Approvals

Title: Approve Spenders Through Off-Chain Signatures on an ERC20 Token

As a token holder
I want to grant spending allowances either directly or by signing a typed permit message
So that a relayer can submit my approval and move my tokens without me paying gas

Acceptance Criteria
1. Deploy the Token
Given a name, a symbol and a number of decimals
When the token is deployed
Then name, symbol and decimals should return those values
And totalSupply should be 0
2. Mint Tokens
Given any caller
When I call mint(to, amount)
Then balanceOf(to) and totalSupply should both increase by amount
And a Transfer event from the zero address to to should be emitted
3. Transfer Tokens
Given I hold at least amount tokens
When I call transfer(to, amount)
Then my balance should decrease and the balance of to should increase by amount
And a Transfer event should be emitted and the call should return true
And the call should fail if my balance is below amount
4. Approve a Spender
Given any account
When I call approve(spender, amount)
Then allowance(me, spender) should equal amount
And an Approval event should be emitted and the call should return true
5. Transfer on Behalf of an Owner
Given from has approved me for at least amount and holds at least amount
When I call transferFrom(from, to, amount)
Then amount should move from from to to and a Transfer event should be emitted
And my allowance should decrease by amount unless it equals the maximum uint256 value, in which case it should stay unchanged
And the call should revert if the allowance or the balance of from is insufficient
6. Approve by Signature
Given owner signed an EIP-712 Permit(owner, spender, value, nonce, deadline) message with the current nonces(owner)
When anyone calls permit(owner, spender, value, deadline, v, r, s)
Then allowance(owner, spender) should equal value and nonces(owner) should increase by 1
And an Approval event should be emitted
And the call should revert with "PERMIT_DEADLINE_EXPIRED" if deadline is earlier than the current block timestamp
And it should revert with "INVALID_SIGNER" if the signature does not recover to owner, including when the same signature is submitted a second time
7. Read the Domain Separator
Given the token is deployed
When anyone calls DOMAIN_SEPARATOR
Then it should return the EIP-712 domain hash built from the token name, version "1", the current chain id and the token address

Notes
The EIP-712 domain is name = token name, version = "1", chainId, verifyingContract = token address; tests can sign permits with signTypedData
The file also contains the abstract base SbeERC20PermitERC20 holding the ERC20 and permit logic; tests only deploy SbeERC20Permit
The token has no burn entry point and no owner role
