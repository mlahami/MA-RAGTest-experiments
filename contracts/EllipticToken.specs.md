User Story: Voucher-Based Token with Signed Permits

Title: Mint Tokens from Owner Vouchers and Approve Spenders with Signed Permits

As a token holder
I want to redeem vouchers issued by the token owner and authorize spenders with signatures
So that tokens are only minted and approved with the consent of the right parties

Acceptance Criteria
1. Deploy the Token
Given the token is deployed
Then name should be "EllipticToken", symbol "ETK" and decimals 18
And the deployer should be the owner
2. Redeem a Voucher
Given voucherHash = keccak256(abi.encodePacked(amount, receiver, salt)) signed by the owner and by the receiver
When anyone calls redeemVoucher(amount, receiver, salt, ownerSignature, receiverSignature)
Then amount tokens should be minted to receiver and voucherHash marked in usedHashes
And redeeming the same voucher again should revert with HashAlreadyUsed
And a signature not from the owner should revert with InvalidOwner, and one not from receiver with InvalidReceiver
3. Approve by Permit
Given a token holder signed a permit for amount and spender signed keccak256(abi.encodePacked(tokenOwner, spender, amount))
When anyone calls permit(amount, spender, tokenOwnerSignature, spenderSignature)
Then allowance(tokenOwner, spender) should equal amount and an Approval event should be emitted
And the permit should be marked as used so that replaying it reverts with HashAlreadyUsed
And a spender signature from another account should revert with InvalidSpender
4. Require the Holder's Explicit Consent
Given a holder who never signed a permit for a given amount
When anyone calls permit with a tokenOwnerSignature that recovers to that holder
Then no allowance over the holder's tokens should be granted unless the holder deliberately signed that permit
And signatures the holder produced for other purposes, such as accepting a voucher, must never result in an allowance
5. Reject Malformed Signatures
Given a signature of wrong length or invalid content
When it is passed to redeemVoucher or permit
Then the call should revert with ECDSAInvalidSignatureLength, ECDSAInvalidSignatureS or ECDSAInvalidSignature
6. Standard Token and Ownership Operations
Given I hold ETK
When I call transfer, approve or transferFrom
Then they should behave as a standard OpenZeppelin ERC20 (ERC20InsufficientBalance, ERC20InsufficientAllowance)
And the owner can transferOwnership or renounceOwnership; other callers get OwnableUnauthorizedAccount

Notes
All signatures are 65-byte ECDSA signatures over the raw 32-byte hash, without the Ethereum signed message prefix; tests sign digests with a SigningKey
The permit message signed by the token holder is the 32-byte value of amount
usedHashes is a public getter
