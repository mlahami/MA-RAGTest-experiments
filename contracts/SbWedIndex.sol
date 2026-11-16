// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0x84d9ec85c9c568eb332b7226a8f826d897e0a4a8.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbWedIndexOwned {

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    address public owner;

    constructor() {
        owner = msg.sender;
    }

    address public newOwner;

    function changeOwner(address _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }

    function acceptOwnership() public {
        if (msg.sender == newOwner) {
            owner = newOwner;
        }
    }

    function execute(address _dst, uint _value, bytes memory _data) public onlyOwner {
        _dst.call{value: _value}(_data);
    }
}

contract SbWedIndex is SbWedIndexOwned {

    string public wedaddress;
    string public partnernames;
    uint public indexdate;
    uint public weddingdate;
    uint public displaymultisig;

    IndexArray[] public indexarray;

    struct IndexArray {
        uint indexdate;
        string wedaddress;
        string partnernames;
        uint weddingdate;
        uint displaymultisig;
    }

    function numberOfIndex() view public returns (uint) {
        return indexarray.length;
    }

    function writeIndex(uint indexdate, string memory wedaddress, string memory partnernames, uint weddingdate, uint displaymultisig) public {
        indexarray.push(IndexArray(block.timestamp, wedaddress, partnernames, weddingdate, displaymultisig));
        emit IndexWritten(block.timestamp, wedaddress, partnernames, weddingdate, displaymultisig);
    }

    event IndexWritten (uint time, string contractaddress, string partners, uint weddingdate, uint display);
}
