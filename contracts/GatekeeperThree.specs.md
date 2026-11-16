User Story: Three-Gate Entrance Registry

Title: Register as Entrant After Passing Three Access Gates

As a participant who wants to be registered as the entrant of the gatekeeper
I want to pass the ownership, password and payment gates of the GatekeeperThree contract
So that my externally owned account is recorded as the official entrant

Acceptance Criteria
1. Register the Owner
Given the GatekeeperThree contract is deployed
When an account calls construct0r
Then the caller should be stored as the owner
And the owner should be readable through the public owner getter
2. Create the Password Helper
Given the contract is deployed
When an account calls createTrick
Then a new SimpleTrick helper should be deployed and linked to this gatekeeper
And its address should be readable through the public trick getter
3. Unlock the Entrance with the Password
Given the SimpleTrick helper has been created
When an account calls getAllowance with the correct password stored in the helper
Then allowEntrance should become true
And when the password is wrong, allowEntrance should remain unchanged and the helper should refresh its password to the current block timestamp
4. Fund the Gatekeeper
Given the contract can receive Ether
When any account sends Ether to the contract with empty calldata
Then the Ether should be accepted and the contract balance should increase
5. Gate One: Owner Acting Through a Contract
Given an account calls enter
When msg.sender is not the owner, or tx.origin is the owner
Then the transaction should revert
6. Gate Two: Entrance Allowed
Given gate one is satisfied
When allowEntrance is false
Then the call to enter should revert
7. Gate Three: Balance and Payment Condition
Given gates one and two are satisfied
When the contract balance is greater than 0.001 ether and sending 0.001 ether to the owner fails
Then the entrant should be set to tx.origin
And when this condition is not met, the call should complete without changing the entrant
8. Read the State
Given I want to inspect the gatekeeper
When I query owner, entrant, allowEntrance and trick
Then I should receive their current values
Notes
SimpleTrick is a helper contract in the same file, created by createTrick; it holds the password and exposes checkPassword, trickInit and trickyTrick; tests use it only through createTrick and getAllowance
The entrant is always the transaction origin, not the intermediate contract
No events are emitted by this contract
None of the require checks have revert messages
