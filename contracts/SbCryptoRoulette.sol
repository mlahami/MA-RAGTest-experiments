// Benchmark candidate ported from smartbugs-curated: dataset/other/crypto_roulette.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbCryptoRoulette {

    uint256 private secretNumber;
    uint256 public lastPlayed;
    uint256 public betPrice = 0.1 ether;
    address public ownerAddr;

    struct Game {
        address player;
        uint256 number;
    }
    Game[] public gamesPlayed;

    constructor() {
        ownerAddr = msg.sender;
        shuffle();
    }

    function shuffle() internal {
        secretNumber = uint8(uint256(keccak256(abi.encodePacked(block.timestamp, blockhash(block.number-1))))) % 20 + 1;
    }

    function play(uint256 number) payable public {
        require(msg.value >= betPrice && number <= 10);
        Game storage game;
        assembly { game.slot := 0 }
        game.player = msg.sender;
        game.number = number;
        gamesPlayed.push(game);

        if (number == secretNumber) {
            payable(msg.sender).transfer(address(this).balance);
        }

        shuffle();
        lastPlayed = block.timestamp;
    }

    function kill() public {
        if (msg.sender == ownerAddr && block.timestamp > lastPlayed + 1 days) {
            selfdestruct(payable(msg.sender));
        }
    }

    receive() external payable { }
}
