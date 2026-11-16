User Story: Signature-Authorized Bank Withdrawal

Title: Withdraw a Fixed Amount of Ether After Proving Ownership with Signatures

As a bank customer
I want to withdraw 1 ETH from the bank by presenting signatures made with my own key
So that only a caller who proves control of their address with valid signatures can receive funds

Acceptance Criteria
1. Fund the Bank
Given the SimpleBank contract is deployed
When any account sends Ether to the contract with empty calldata
Then the Ether should be accepted and the bank balance should increase
2. Verify a Single Signature
Given I hold a Signature made of hash, v, r and s
When I call verifySignatures with it
Then the call should succeed if ecrecover(hash, v, r, s) equals my address
And it should revert with "Invalid signature" otherwise
3. Withdraw with Valid Signatures
Given the bank holds at least 1 ETH
And I provide a non-empty array of signatures, each signed by my own address
When I call withdraw with that array
Then every signature should be verified against my address
And exactly 1 ETH should be transferred to me
4. Require Proof of Ownership
Given I call withdraw
When the array contains no signatures
Then the withdrawal should be rejected and no Ether should be sent
5. Reject Invalid Signatures
Given at least one signature in the array does not recover to my address
When I call withdraw
Then the transaction should revert with "Invalid signature"
And the bank balance should not change
6. Insufficient Bank Funds
Given the bank holds less than 1 ETH
When I call withdraw with valid signatures
Then the transaction should revert
Notes
Each successful withdrawal pays a fixed 1 ETH, regardless of the number of signatures
The bank does not track per-user deposits or emit events
Signatures are checked against msg.sender, so a signature signed by another key is always invalid
