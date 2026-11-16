User Story: Deposit Vault with Owner Proxy Calls

Title: Deposit Ether into a Vault and Relay Calls Through the Vault

As a vault user
I want to deposit Ether that is tracked per account, and to relay calls with Ether through the vault
So that my deposits are recorded and I can interact with other contracts via the vault

Acceptance Criteria
1. Deploy the Vault
Given a deployer
When the contract is deployed
Then the deployer should be the proxy administrator able to use owner-restricted functions
And the public Owner variable should be the zero address until the vault is initialised
2. Initialise the Vault
Given an externally owned account
When it calls Vault, optionally sending Ether
Then it should be recorded as the public Owner
And the sent Ether should be processed as a deposit
And when the caller is a contract nothing should change
3. Deposit
Given any account
When it calls deposit sending more than 0.5 ETH
Then its entry in Deposits should increase by the amount sent
And deposits of 0.5 ETH or less should not be credited
4. Receive Plain Ether
Given any account
When it sends plain Ether
Then the contract should accept it without crediting a deposit
5. Withdraw
Given I am the administrator and my recorded deposit is at least the requested amount
When I call withdraw with an amount greater than zero
Then that amount should be transferred to me
And when the amount is zero or exceeds my deposit, nothing should be paid
And calls from other accounts should have no effect
6. Transfer Administration
Given I am the administrator
When I call transferOwner with a new address
Then the new address should become the administrator
And calls from other accounts should have no effect
7. Relay a Call
Given any account
When it calls proxy with a target, call data and attached Ether
Then the target should be called with that data and the attached Ether forwarded
And if the target call fails the whole proxy transaction should be reverted
And the attached Ether should be returned to the caller rather than staying in the vault

Notes
Restricted functions silently do nothing for unauthorised callers instead of reverting
Deposits are tracked per address in the public Deposits mapping
Withdrawals do not reduce the recorded deposit
