User Story: English Auction for an NFT

Title: Auction an NFT to the Highest Ether Bidder Over Seven Days

As an NFT seller or bidder
I want to run an ascending-price auction for a single NFT paid in Ether
So that the NFT goes to the highest bidder and outbid participants can recover their Ether

Acceptance Criteria
1. Create the Auction
Given I own an NFT
When I deploy EnglishAuction with the NFT address, nftId and a startingBid
Then I should be recorded as seller
And highestBid should equal startingBid
And started and ended should be false
2. Start the Auction
Given I am the seller and I approved the contract for the NFT
When I call start
Then the NFT should be transferred from me to the contract
And started should be true and endAt set to the current time plus 7 days
And a Start event should be emitted
And if the auction already started the call reverts with "started"
And if I am not the seller it reverts with "not seller"
3. Place a Bid
Given the auction has started and not reached endAt
When I call bid sending Ether greater than highestBid
Then I become highestBidder and highestBid equals my value
And the previous highest bidder's bid is added to their withdrawable bids balance
And a Bid event should be emitted with sender and amount
And the call reverts with "not started" before start, "ended" at or after endAt, and "value < highest" if my value is not strictly higher
4. Withdraw an Outbid Amount
Given I have been outbid
When I call withdraw
Then my withdrawable bids balance should be sent to me and reset to zero
And a Withdraw event should be emitted with the amount
5. End the Auction
Given the auction started and endAt has passed
When anyone calls end
Then ended should be true
And if there is a highest bidder the NFT goes to that bidder and highestBid is sent to the seller
And if there were no bids the NFT returns to the seller
And an End event should be emitted with the winner and amount
And the call reverts with "not started", "not ended" before endAt, or "ended" if already ended

Notes
The auction lasts exactly 7 days from start
The current highest bid stays in the contract until the auction ends
Calling withdraw with no balance transfers zero
The test environment provides EnglishAuctionMockNFT (mintable by anyone via mint(to, tokenId), with approve and transferFrom) to supply the NFT whose address and id are passed to the EnglishAuction constructor
