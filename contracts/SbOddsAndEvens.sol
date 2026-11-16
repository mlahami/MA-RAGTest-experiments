// Benchmark candidate ported from smartbugs-curated: dataset/front_running/odds_and_evens.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbOddsAndEvens{

  struct Player {
    address addr;
    uint number;
  }

  Player[2] public players;

  uint8 tot;
  address owner;

  constructor() {
    owner = msg.sender;
  }
  function play(uint number) public payable{
    if (msg.value != 1 ether) revert();
    players[tot] = Player(msg.sender, number);
    tot++;

    if (tot==2) andTheWinnerIs();
  }

  function andTheWinnerIs() private {
    bool res ;
    uint n = players[0].number+players[1].number;
    if (n%2==0) {
      res = payable(players[0].addr).send(1.8 ether);
    }
    else {
      res = payable(players[1].addr).send(1.8 ether);
    }

    delete players;
    tot=0;
  }

  function getProfit() public {
    if(msg.sender!=owner) revert();
    bool res = payable(msg.sender).send(address(this).balance);
  }

}
