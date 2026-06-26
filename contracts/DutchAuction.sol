// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DutchAuction {
    struct Bid {
        address bidder;
        uint256 amount;
        uint256 pricePaid;
        bool refunded;
    }

    address public seller;
    uint256 public startPrice;
    uint256 public reservePrice;
    uint256 public startTime;
    uint256 public duration;
    uint256 public totalSupply;
    uint256 public sold;
    bool public settled;
    bool public whitelistEnabled;
    bool private _locked;

    mapping(address => bool) public whitelist;
    mapping(address => uint256) public pendingRefunds;
    Bid[] public bids;

    event BidPlaced(address indexed bidder, uint256 qty, uint256 price, uint256 total);
    event AuctionSettled(uint256 clearingPrice, uint256 totalSold);
    event Refunded(address indexed bidder, uint256 amount);
    event Withdrawn(address indexed seller, uint256 amount);

    modifier onlySeller() { require(msg.sender == seller, "Not seller"); _; }
    modifier noReentrant() { require(!_locked, "Reentrant"); _locked = true; _; _locked = false; }
    modifier auctionActive() {
        require(block.timestamp >= startTime, "Not started");
        require(block.timestamp < startTime + duration, "Ended");
        require(!settled, "Settled");
        _;
    }

    constructor(
        uint256 _startPrice,
        uint256 _reservePrice,
        uint256 _duration,
        uint256 _totalSupply,
        bool _whitelistEnabled
    ) {
        require(_startPrice > _reservePrice, "Invalid prices");
        require(_totalSupply > 0, "Zero supply");
        seller = msg.sender;
        startPrice = _startPrice;
        reservePrice = _reservePrice;
        duration = _duration;
        totalSupply = _totalSupply;
        startTime = block.timestamp;
        whitelistEnabled = _whitelistEnabled;
    }

    function currentPrice() public view returns (uint256) {
        if (block.timestamp <= startTime) return startPrice;
        if (block.timestamp >= startTime + duration) return reservePrice;
        uint256 elapsed = block.timestamp - startTime;
        uint256 drop = ((startPrice - reservePrice) * elapsed) / duration;
        return startPrice - drop;
    }

    function bid(uint256 quantity) external payable noReentrant auctionActive {
        if (whitelistEnabled) require(whitelist[msg.sender], "Not whitelisted");
        require(quantity > 0, "Zero qty");
        require(sold + quantity <= totalSupply, "Exceeds supply");
        uint256 price = currentPrice();
        uint256 totalCost = price * quantity;
        require(msg.value >= totalCost, "Underpaid");
        uint256 excess = msg.value - totalCost;
        sold += quantity;
        bids.push(Bid({
            bidder: msg.sender,
            amount: quantity,
            pricePaid: price,
            refunded: false
        }));
        if (excess > 0) {
            pendingRefunds[msg.sender] += excess;
            emit Refunded(msg.sender, excess);
        }
        emit BidPlaced(msg.sender, quantity, price, totalCost);
        if (sold == totalSupply) _settle();
    }

    function settle() external onlySeller { _settle(); }

    function _settle() internal {
        require(!settled, "Already settled");
        settled = true;
        uint256 clearingPrice = currentPrice();
        for (uint i = 0; i < bids.length; i++) {
            Bid storage b = bids[i];
            if (b.pricePaid > clearingPrice) {
                uint256 refund = (b.pricePaid - clearingPrice) * b.amount;
                pendingRefunds[b.bidder] += refund;
            }
        }
        emit AuctionSettled(clearingPrice, sold);
    }

    function claimRefund() external noReentrant {
        uint256 amount = pendingRefunds[msg.sender];
        require(amount > 0, "No refund");
        pendingRefunds[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok, "Refund failed");
        emit Refunded(msg.sender, amount);
    }

    function withdraw() external noReentrant onlySeller {
        require(settled, "Not settled");
        uint256 clearingPrice = currentPrice();
        uint256 proceeds = clearingPrice * sold;
        (bool ok,) = seller.call{value: proceeds}("");
        require(ok, "Withdraw failed");
        emit Withdrawn(seller, proceeds);
    }

    function addToWhitelist(address[] calldata users) external onlySeller {
        for (uint i = 0; i < users.length; i++) whitelist[users[i]] = true;
    }

    function getBidsCount() external view returns (uint256) { return bids.length; }
}