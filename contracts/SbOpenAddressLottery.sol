// Benchmark candidate ported from smartbugs-curated: dataset/other/open_address_lottery.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbOpenAddressLottery{
    struct SeedComponents{
        uint component1;
        uint component2;
        uint component3;
        uint component4;
    }

    address owner;
    uint private secretSeed;
    uint private lastReseed;
    uint LuckyNumber = 7;

    mapping (address => bool) winner;

    constructor() {
        owner = msg.sender;
        reseed(SeedComponents(uint(uint160(address(block.coinbase))), block.difficulty, block.gaslimit, block.timestamp));
    }

    function participate() public payable {
        if(msg.value<0.1 ether)
            return;

        require(winner[msg.sender] == false);

        if(luckyNumberOfAddress(msg.sender) == LuckyNumber){
            winner[msg.sender] = true;

            uint win=msg.value*7;

            if(win>address(this).balance)
                win=address(this).balance;
            payable(msg.sender).transfer(win);
        }

        if(block.number-lastReseed>1000)
            reseed(SeedComponents(uint(uint160(address(block.coinbase))), block.difficulty, block.gaslimit, block.timestamp));
    }

    function luckyNumberOfAddress(address addr) public view returns(uint n){
        n = uint(uint8(keccak256(abi.encodePacked(uint(uint160(addr)), secretSeed))[0])) % 8;
    }

    function reseed(SeedComponents memory components) internal {
        secretSeed = uint256(keccak256(abi.encodePacked(
            components.component1,
            components.component2,
            components.component3,
            components.component4
        )));
        lastReseed = block.number;
    }

    function kill() public {
        require(msg.sender==owner);

        selfdestruct(payable(msg.sender));
    }

    function forceReseed() public {
        require(msg.sender==owner);
        SeedComponents storage s;
        assembly { s.slot := 0 }
        s.component1 = uint(uint160(msg.sender));
        s.component2 = uint256(blockhash(block.number - 1));
        unchecked { s.component3 = block.difficulty*uint(uint160(address(block.coinbase))); }
        s.component4 = tx.gasprice * 7;

        reseed(s);
    }

    fallback() external payable {
        if(msg.value>=0.1 ether && msg.sender!=owner)
            participate();
    }

}
