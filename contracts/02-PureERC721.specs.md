# PureERC721 — User Stories & Specifications

> **Contract:** `PureERC721.sol`
> **Standards:** EIP-721, EIP-165, On-chain SVG metadata
> **No imports — fully self-contained**
> **Compiler:** Solidity ^0.8.20

---

## Actors

| Actor | Description |
|---|---|
| Owner | Contract deployer; toggles sale and withdraws |
| Collector | Any address that mints or holds an NFT |
| Operator | Address approved for all of a holder's tokens |

---

## US-01 — Toggle public sale

**As an** owner,
**I want** to toggle the sale active/inactive,
**so that** minting is gated until I am ready.

```gherkin
Given saleActive == false
When the owner calls toggleSale()
Then saleActive == true
And a SaleToggled(true) event is emitted

When the owner calls toggleSale() again
Then saleActive == false

Given I am not the owner
When I call toggleSale()
Then the call reverts with NotOwner()
```

---

## US-02 — Mint NFT with ETH payment

**As a** collector,
**I want** to mint an NFT by sending ETH,
**so that** I receive a unique on-chain SVG token.

```gherkin
Given saleActive == true
And totalSupply < maxSupply
And msg.value >= mintPrice
When I call mint()
Then I receive tokenId = previous totalSupply
And ownerOf(tokenId) == me
And totalSupply increments
And onERC721Received is called if recipient is a contract

Given saleActive == false
When I call mint()
Then the call reverts with SaleNotActive()

Given totalSupply >= maxSupply
When I call mint()
Then the call reverts with SoldOut()

Given msg.value < mintPrice
When I call mint()
Then the call reverts with InsufficientPayment(sent, required)
```

---

## US-03 — Owner free-mint

**As an** owner,
**I want** to mint multiple tokens to any address for free,
**so that** I can reserve team/treasury allocations.

```gherkin
Given totalSupply + amount <= maxSupply
When the owner calls ownerMint(to, amount)
Then amount tokens are minted consecutively
And ownerOf each new tokenId == to

Given amount would exceed maxSupply
Then the call reverts with SoldOut() on the overflow iteration
```

---

## US-04 — On-chain SVG metadata

**As a** marketplace,
**I want** to call tokenURI(tokenId) and receive valid base64-encoded JSON,
**so that** the artwork is fully on-chain and needs no external IPFS.

```gherkin
Given tokenId exists
When I call tokenURI(tokenId)
Then the return value starts with "data:application/json;base64,"
And decoded JSON contains "name", "description", and "image" fields
And "image" is a "data:image/svg+xml;base64,..." URI
And the SVG is deterministically generated from tokenId seed

Given tokenId does not exist
When I call tokenURI(tokenId)
Then the call reverts with TokenNotFound(tokenId)
```

---

## US-05 — Transfer and approval

**As a** token holder,
**I want** to transfer my NFT and manage approvals,
**so that** I can sell or delegate control of my tokens.

```gherkin
Given I own tokenId
When I call transferFrom(me, recipient, tokenId)
Then ownerOf(tokenId) == recipient
And token approval is cleared
And a Transfer event is emitted

Given I am not the owner or approved
When I call transferFrom(...)
Then the call reverts with NotAuthorized()

When I call setApprovalForAll(operator, true)
Then isApprovedForAll(me, operator) == true
And operator can transfer any of my tokens
```

---

## US-06 — EIP-165 interface detection

**As a** smart contract,
**I want** to call supportsInterface to detect ERC-721 compliance,
**so that** I can safely interact with this contract.

```gherkin
When I call supportsInterface(0x80ac58cd)  # ERC721
Then returns true
When I call supportsInterface(0x5b5e139f)  # ERC721Metadata
Then returns true
When I call supportsInterface(0x01ffc9a7)  # ERC165
Then returns true
When I call supportsInterface(0xdeadbeef)
Then returns false
```

---

## Security Properties

| Property | Detail |
|---|---|
| Safe mint | `_checkOnERC721Received` called on contract recipients |
| Sale gate | `SaleNotActive` error; owner-toggled |
| Supply cap | checked before mint, reverts with `SoldOut` |
| Approval clear | Token approval deleted on every transfer |
| Self-contained base64 | Inline assembly base64 encoder — no external libs |
