User Story: Signature-Governed Ether Vault

Title: Appoint an Admin and Lock Funds Only with the Owner's Signatures

As the owner of an ether vault
I want administrative changes to require my off-chain signature over nonce-bound messages
So that only an admin I approved can withdraw, and only when I have not locked the funds

Acceptance Criteria
1. Deploy the Vault
Given the vault is deployed, optionally with ether
Then the deployer should be the owner
And admin should be the zero address, nonce should be 0 and the funds should be unlocked
2. Hash a Message
Given any message string
When anyone calls hash_message(message)
Then it should return the Ethereum signed message hash ("\x19Ethereum Signed Message:\n" + byte length + message)
3. Appoint an Admin
Given the owner signed the message "admin" + decimal nonce + the 20 raw bytes of newAdmin
When anyone calls setAdmin(signature, newAdmin)
Then admin should become newAdmin and nonce should increase by 1
And a signature not produced by the owner for that exact message and the current nonce should revert with InvalidSignature
And malformed signatures should revert with ECDSAInvalidSignature, ECDSAInvalidSignatureLength or ECDSAInvalidSignatureS
4. Toggle the Lock
Given the owner signed the message "lock" + decimal nonce
When anyone calls switchLock(signature)
Then the lock state should flip and nonce should increase by 1
And an invalid signature should revert with InvalidSignature
5. Prevent Replay
Given a signature was already accepted
When it is submitted again
Then it should revert with InvalidSignature because nonce has changed
6. Withdraw Funds
Given I am the admin and the funds are unlocked
When I call withdraw
Then the whole ether balance of the vault should be sent to me
And a caller other than admin should be rejected with NotAdmin
And if the funds are locked the call should revert with FundsLocked
7. Ownership
Given I am the owner
When I call transferOwnership or renounceOwnership
Then the signing authority should move to the new owner (or nobody); other callers get OwnableUnauthorizedAccount

Notes
ImpersonatorTwoStrings is an in-file helper library (decimal conversion and message hashing) used internally; tests do not call it
Tests produce signatures with signMessage over the raw message bytes, for example concat(toUtf8Bytes("admin0"), newAdmin)
The vault accepts ether only at deployment; there is no receive function
