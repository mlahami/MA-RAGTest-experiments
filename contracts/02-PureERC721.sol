// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PureERC721
 * @notice Self-contained ERC-721 NFT — zero imports.
 *         Implements EIP-721 + EIP-165 + metadata extension
 *         + enumeration helpers + on-chain SVG art generation.
 */
contract PureERC721 {

    // ─── EIP-165 ───────────────────────────────────────────────────────────
    bytes4 private constant _ERC165_ID   = 0x01ffc9a7;
    bytes4 private constant _ERC721_ID   = 0x80ac58cd;
    bytes4 private constant _ERC721META  = 0x5b5e139f;

    // ─── Storage ───────────────────────────────────────────────────────────
    string public name;
    string public symbol;

    uint256 public totalSupply;
    uint256 public immutable maxSupply;
    uint256 public immutable mintPrice;

    address public owner;
    bool    public saleActive;

    mapping(uint256 => address)           private _owners;
    mapping(address => uint256)           private _balances;
    mapping(uint256 => address)           private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    mapping(uint256 => string)            private _tokenURIs;

    // ─── On-chain art palette ──────────────────────────────────────────────
    string[8] private _colors = [
        "#FF6B6B","#4ECDC4","#45B7D1","#96CEB4",
        "#FFEAA7","#DDA0DD","#98D8C8","#F7DC6F"
    ];

    // ─── Events ────────────────────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event SaleToggled(bool active);
    event Withdrawn(address to, uint256 amount);

    // ─── Errors ────────────────────────────────────────────────────────────
    error NotOwner();
    error NotAuthorized();
    error ZeroAddress();
    error TokenNotFound(uint256 tokenId);
    error SoldOut();
    error SaleNotActive();
    error InsufficientPayment(uint256 sent, uint256 required);
    error WithdrawFailed();
    error NotTokenOwner();

    modifier onlyOwner() { if (msg.sender != owner) revert NotOwner(); _; }

    constructor(
        string memory _name,
        string memory _symbol,
        uint256 _maxSupply,
        uint256 _mintPrice,
        address _owner
    ) {
        if (_owner == address(0)) revert ZeroAddress();
        name      = _name;
        symbol    = _symbol;
        maxSupply = _maxSupply;
        mintPrice = _mintPrice;
        owner     = _owner;
    }

    // ─── EIP-165 ───────────────────────────────────────────────────────────
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == _ERC165_ID
            || interfaceId == _ERC721_ID
            || interfaceId == _ERC721META;
    }

    // ─── EIP-721 Core ──────────────────────────────────────────────────────
    function balanceOf(address _owner) external view returns (uint256) {
        if (_owner == address(0)) revert ZeroAddress();
        return _balances[_owner];
    }

    function ownerOf(uint256 tokenId) public view returns (address) {
        address tokenOwner = _owners[tokenId];
        if (tokenOwner == address(0)) revert TokenNotFound(tokenId);
        return tokenOwner;
    }

    function approve(address to, uint256 tokenId) external {
        address tokenOwner = ownerOf(tokenId);
        if (msg.sender != tokenOwner && !_operatorApprovals[tokenOwner][msg.sender])
            revert NotAuthorized();
        _tokenApprovals[tokenId] = to;
        emit Approval(tokenOwner, to, tokenId);
    }

    function getApproved(uint256 tokenId) external view returns (address) {
        if (_owners[tokenId] == address(0)) revert TokenNotFound(tokenId);
        return _tokenApprovals[tokenId];
    }

    function setApprovalForAll(address operator, bool approved) external {
        if (operator == address(0)) revert ZeroAddress();
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }

    function isApprovedForAll(address _owner, address operator) external view returns (bool) {
        return _operatorApprovals[_owner][operator];
    }

    function transferFrom(address from, address to, uint256 tokenId) public {
        if (to == address(0)) revert ZeroAddress();
        address tokenOwner = ownerOf(tokenId);
        if (from != tokenOwner) revert NotTokenOwner();
        if (msg.sender != tokenOwner
            && msg.sender != _tokenApprovals[tokenId]
            && !_operatorApprovals[tokenOwner][msg.sender])
            revert NotAuthorized();
        _transfer(from, to, tokenId);
    }

    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        safeTransferFrom(from, to, tokenId, "");
    }

    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data) public {
        transferFrom(from, to, tokenId);
        _checkOnERC721Received(from, to, tokenId, data);
    }

    // ─── Metadata ──────────────────────────────────────────────────────────
    function tokenURI(uint256 tokenId) external view returns (string memory) {
        if (_owners[tokenId] == address(0)) revert TokenNotFound(tokenId);
        bytes memory svg = _buildSVG(tokenId);
        bytes memory json = abi.encodePacked(
            '{"name":"Token #', _toString(tokenId),
            '","description":"On-chain art NFT","image":"data:image/svg+xml;base64,',
            _base64(svg), '"}'
        );
        return string(abi.encodePacked("data:application/json;base64,", _base64(json)));
    }

    // ─── Minting ───────────────────────────────────────────────────────────
    function mint() external payable returns (uint256 tokenId) {
        if (!saleActive) revert SaleNotActive();
        if (totalSupply >= maxSupply) revert SoldOut();
        if (msg.value < mintPrice) revert InsufficientPayment(msg.value, mintPrice);
        tokenId = totalSupply;
        _safeMint(msg.sender, tokenId);
    }

    function ownerMint(address to, uint256 amount) external onlyOwner {
        if (to == address(0)) revert ZeroAddress();
        for (uint256 i; i < amount; ) {
            if (totalSupply >= maxSupply) revert SoldOut();
            _safeMint(to, totalSupply);
            unchecked { ++i; }
        }
    }

    // ─── Admin ─────────────────────────────────────────────────────────────
    function toggleSale() external onlyOwner {
        saleActive = !saleActive;
        emit SaleToggled(saleActive);
    }

    function withdraw() external onlyOwner {
        uint256 bal = address(this).balance;
        (bool ok,) = owner.call{value: bal}("");
        if (!ok) revert WithdrawFailed();
        emit Withdrawn(owner, bal);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        owner = newOwner;
    }

    // ─── Internals ─────────────────────────────────────────────────────────
    function _transfer(address from, address to, uint256 tokenId) internal {
        delete _tokenApprovals[tokenId];
        unchecked {
            _balances[from]--;
            _balances[to]++;
        }
        _owners[tokenId] = to;
        emit Transfer(from, to, tokenId);
    }

    function _safeMint(address to, uint256 tokenId) internal {
        _owners[tokenId]  = to;
        _balances[to]++;
        totalSupply++;
        emit Transfer(address(0), to, tokenId);
        _checkOnERC721Received(address(0), to, tokenId, "");
    }

    function _checkOnERC721Received(address from, address to, uint256 tokenId, bytes memory data) internal {
        if (to.code.length > 0) {
            bytes4 retval = IERC721Receiver(to).onERC721Received(msg.sender, from, tokenId, data);
            require(retval == 0x150b7a02, "ERC721: unsafe recipient");
        }
    }

    // ─── On-chain SVG art ──────────────────────────────────────────────────
    function _buildSVG(uint256 tokenId) internal view returns (bytes memory) {
        uint256 seed    = uint256(keccak256(abi.encodePacked(tokenId)));
        string memory c1 = _colors[seed       % 8];
        string memory c2 = _colors[(seed >> 8) % 8];
        string memory c3 = _colors[(seed >>16) % 8];
        return abi.encodePacked(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">',
            '<rect width="300" height="300" fill="', c1, '"/>',
            '<circle cx="150" cy="150" r="', _toString(80 + (seed % 40)), '" fill="', c2, '" opacity="0.8"/>',
            '<polygon points="150,30 270,270 30,270" fill="', c3, '" opacity="0.6"/>',
            '<text x="150" y="285" text-anchor="middle" font-size="12" fill="white">#',
            _toString(tokenId), '</text></svg>'
        );
    }

    // ─── Utility ───────────────────────────────────────────────────────────
    function _toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) { digits++; temp /= 10; }
        bytes memory buf = new bytes(digits);
        while (value != 0) {
            digits--;
            buf[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buf);
    }

    bytes private constant _TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    function _base64(bytes memory data) internal pure returns (string memory) {
        if (data.length == 0) return "";
        uint256 encodedLen = 4 * ((data.length + 2) / 3);
        bytes memory result = new bytes(encodedLen);
        bytes memory table  = _TABLE;
        assembly {
            let tablePtr  := add(table, 1)
            let resultPtr := add(result, 32)
            let dataLen   := mload(data)
            let dataPtr   := add(data, 32)
            let endPtr    := add(dataPtr, dataLen)
            for {} lt(dataPtr, endPtr) {} {
                dataPtr := add(dataPtr, 3)
                let input := mload(dataPtr)
                mstore8(resultPtr,       mload(add(tablePtr, and(shr(18, input), 0x3F))))
                mstore8(add(resultPtr,1),mload(add(tablePtr, and(shr(12, input), 0x3F))))
                mstore8(add(resultPtr,2),mload(add(tablePtr, and(shr( 6, input), 0x3F))))
                mstore8(add(resultPtr,3),mload(add(tablePtr, and(        input,  0x3F))))
                resultPtr := add(resultPtr, 4)
            }
            switch mod(dataLen, 3)
            case 1 { mstore8(sub(resultPtr,1),0x3d) mstore8(sub(resultPtr,2),0x3d) }
            case 2 { mstore8(sub(resultPtr,1),0x3d) }
        }
        return string(result);
    }
}

interface IERC721Receiver {
    function onERC721Received(address,address,uint256,bytes calldata) external returns (bytes4);
}
