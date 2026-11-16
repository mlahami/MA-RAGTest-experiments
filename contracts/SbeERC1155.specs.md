User Story: ERC1155 Multi-Token

Title: Hold, Approve and Transfer Multiple Token Types Following the ERC1155 Standard

As a multi-token holder or approved operator
I want to query balances for many token ids, approve operators and transfer one or several token types at once
So that fungible and non-fungible tokens can be managed in a single contract according to the ERC1155 standard

Acceptance Criteria
1. Query Balances
Given an owner and a token id
When I call balanceOf(owner, id)
Then I should receive the owner's balance of that id
And balanceOfBatch(owners, ids) returns the balance for each owner/id pair
And balanceOfBatch reverts with "owners length != ids length" if the arrays differ in length
2. Approve an Operator
Given I am any account
When I call setApprovalForAll with an operator and a boolean
Then isApprovedForAll(me, operator) should equal the boolean
And an ApprovalForAll event should be emitted
3. Transfer a Single Token Type
Given I am from or an operator approved by from
When I call safeTransferFrom with from, to, id, value and data
Then from's balance of id decreases by value and to's balance increases by value
And a TransferSingle event should be emitted with operator, from, to, id and value
And the call reverts with "not approved" if I am neither from nor an approved operator, and "to = 0 address" if to is zero
And the call fails if from's balance is insufficient
And if to is a contract it must return the onERC1155Received selector, otherwise the call reverts with "unsafe transfer"
4. Transfer Several Token Types
Given I am from or an operator approved by from
When I call safeBatchTransferFrom with from, to, ids, values and data
Then each balance is moved as in a single transfer
And one TransferBatch event should be emitted with the ids and values
And the call reverts with "not approved", "to = 0 address" or "ids length != values length" when the respective condition is not met
And if to is a contract it must return the onERC1155BatchReceived selector, otherwise the call reverts with "unsafe transfer"
5. Interface Support and Metadata
Given the contract is deployed
When I call supportsInterface
Then it returns true for 0x01ffc9a7 (ERC165), 0xd9b67a26 (ERC1155) and 0x0e89341c (metadata URI) and false otherwise
And uri(id) returns an empty string in this base contract

6. Mint Tokens
Given any account
When I call mint with a recipient, a token id, an amount and data
Then the recipient's balance for that id should increase by the amount
And a TransferSingle event from the zero address should be emitted
And when I call batchMint with lists of ids and amounts, every listed balance should increase and a TransferBatch event should be emitted
And minting to the zero address should fail with "to = 0 address"
And batch minting with lists of different lengths should fail with "ids length != values length"
And minting to a contract recipient that does not accept the tokens should fail with "unsafe transfer"
7. Burn Tokens
Given I hold tokens
When I call burn with a token id and an amount, or batchBurn with lists of ids and amounts
Then my balances should decrease by the given amounts
And a TransferSingle or TransferBatch event to the zero address should be emitted
And burning more than I hold should fail
And batch burning with lists of different lengths should fail with "ids length != values length"
Notes
Minting is open to any account so that balances can be created in a test environment; each holder can only burn their own tokens
Transfers to externally owned accounts are not checked by a receiver hook
