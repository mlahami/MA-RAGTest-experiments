User Story: Paid NFT Collection Minting

Title: Mint Several Collection NFTs at a Fixed Price per Token

As a collector
I want to mint one or more HarToken NFTs in a single transaction by paying 1 ether for each token
So that I can acquire several collection items at once at the announced price

Acceptance Criteria
1. Deploy the Collection
Given the collection is deployed (optionally with ether)
Then name should be "HarToken" and symbol "HRT"
And the deployer should be the owner
And no token should exist yet
2. Mint Tokens
Given I send enough ether
When I call safeMint(to, amount)
Then amount new tokens with consecutive ids starting at the next unused id (first id 0) should be minted to to
And balanceOf(to) should increase by amount and a Transfer event from the zero address should be emitted for each token
3. Charge the Mint Price per Token
Given the mint price is 1 ether per token
When I call safeMint(to, amount)
Then the call should succeed only if msg.value is at least amount * 1 ether
And otherwise it should revert with "Insufficient Ether."
4. Validate the Amount
Given any caller
When I call safeMint with amount 0
Then it should revert with "Must give a mint amount."
And it should revert with "Cannot mint given amount." if the number of minted tokens plus amount would reach 10000
5. Mint to Contracts Safely
Given to is a contract
When tokens are minted to it
Then to must implement onERC721Received and return its selector
And otherwise the call should revert with ERC721InvalidReceiver
And minting to the zero address should revert with ERC721InvalidReceiver
6. Standard NFT Operations
Given I own a token
When I call approve, setApprovalForAll, transferFrom or safeTransferFrom
Then they should behave as a standard OpenZeppelin ERC721
And ownerOf, getApproved and tokenURI of a non-existent token should revert with ERC721NonexistentToken, and tokenURI should return an empty string for existing tokens
And unauthorized transfers should revert with ERC721InsufficientApproval
7. Ownership
Given I am the owner
When I call transferOwnership or renounceOwnership
Then ownership should change accordingly, and other callers should get OwnableUnauthorizedAccount

Notes
HerTokenERC721 is the in-file abstract ERC721 base used by HerToken; tests only deploy HerToken
Ether paid for minting stays in the contract; there is no withdrawal function
supportsInterface reports ERC165, ERC721 and ERC721Metadata
