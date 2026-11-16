User Story: ERC721 Non-Fungible Token

Title: Own, Approve and Transfer Unique Tokens Following the ERC721 Standard

As an NFT owner or approved operator
I want to query ownership, grant approvals and transfer unique tokens safely
So that NFTs can be exchanged between accounts and contracts according to the ERC721 standard

Acceptance Criteria
1. Query Ownership and Balances
Given a token id
When I call ownerOf(id)
Then I should receive its owner
And if the token does not exist the call reverts with "token doesn't exist"
And balanceOf(owner) returns the number of tokens held, reverting with "owner = zero address" for the zero address
2. Interface Support
Given the contract is deployed
When I call supportsInterface
Then it returns true for the ERC721 and ERC165 interface ids and false otherwise
3. Approve a Single Token
Given I am the owner of a token or an operator approved for all of the owner's tokens
When I call approve with a spender and the token id
Then getApproved(id) should return the spender
And an Approval event should be emitted with owner, spender and id
And if I am neither the owner nor an approved operator the call reverts with "not authorized"
And getApproved reverts with "token doesn't exist" for a non-existent token
4. Approve an Operator
Given I am any account
When I call setApprovalForAll with an operator and a boolean
Then isApprovedForAll(me, operator) should equal the boolean
And an ApprovalForAll event should be emitted
5. Transfer a Token
Given I am the owner, the approved address or an approved operator
When I call transferFrom with from, to and id
Then ownership moves to to, from's balance decreases and to's balance increases
And the single-token approval is cleared
And a Transfer event should be emitted
And the call reverts with "from != owner" if from is not the owner, "transfer to zero address" if to is zero, and "not authorized" if I am not allowed
6. Safe Transfer
Given the same conditions as transferFrom
When I call safeTransferFrom, with or without data
Then the token is transferred as in transferFrom
And if to is a contract it must return the onERC721Received selector, otherwise the call reverts with "unsafe recipient"
And transfers to externally owned accounts succeed without a check

7. Mint a Token
Given any account
When I call mint with a recipient address and a token id
Then the recipient should become the owner of that token id
And the recipient's balance should increase by one
And a Transfer event from the zero address should be emitted
And minting to the zero address should fail with "mint to zero address"
And minting an id that already exists should fail with "already minted"
8. Burn a Token
Given I own a token
When I call burn with its id
Then the token should no longer have an owner and its approval should be cleared
And my balance should decrease by one
And a Transfer event to the zero address should be emitted
And burning a token I do not own should fail with "not owner"
Notes
Minting is open to any account so that the collection can be populated in a test environment; burning is restricted to the token owner
Internal minting rejects the zero address ("mint to zero address") and existing ids ("already minted")
