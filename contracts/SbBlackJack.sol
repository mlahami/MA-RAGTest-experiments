// Benchmark candidate ported from smartbugs-curated: dataset/bad_randomness/blackjack.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

library SbBlackJackDeck {

	function deal(address player, uint8 cardNumber) internal view returns (uint8) {
		uint b = block.number;
		uint timestamp = block.timestamp;
		return uint8(uint256(keccak256(abi.encodePacked(blockhash(b), player, cardNumber, timestamp))) % 52);
	}

	function valueOf(uint8 card, bool isBigAce) internal pure returns (uint8) {
		uint8 value = card / 4;
		if (value == 0 || value == 11 || value == 12) {
			return 10;
		}
		if (value == 1 && isBigAce) {
			return 11;
		}
		return value;
	}

	function isAce(uint8 card) internal pure returns (bool) {
		return card / 4 == 1;
	}

	function isTen(uint8 card) internal pure returns (bool) {
		return card / 4 == 10;
	}
}


contract SbBlackJack {
	using SbBlackJackDeck for *;

	uint public minBet = 0.05 ether;
	uint public maxBet = 5 ether;

	uint8 BLACKJACK = 21;

  enum GameState { Ongoing, Player, Tie, House }

	struct Game {
		address player;
		uint bet;

		uint8[] houseCards;
		uint8[] playerCards;

		GameState state;
		uint8 cardsDealt;
	}

	mapping (address => Game) public games;

	modifier gameIsGoingOn() {
		if (games[msg.sender].player == address(0) || games[msg.sender].state != GameState.Ongoing) {
			revert();
		}
		_;
	}

	event Deal(
        bool isUser,
        uint8 _card
    );

    event GameStatus(
    	uint8 houseScore,
    	uint8 houseScoreBig,
    	uint8 playerScore,
    	uint8 playerScoreBig
    );

    event Log(
    	uint8 value
    );

	constructor() {

	}

	receive() external payable {

	}

	function deal() public payable {
		if (games[msg.sender].player != address(0) && games[msg.sender].state == GameState.Ongoing) {
			revert();
		}

		if (msg.value < minBet || msg.value > maxBet) {
			revert();
		}

		uint8[] memory houseCards = new uint8[](1);
		uint8[] memory playerCards = new uint8[](2);

		playerCards[0] = SbBlackJackDeck.deal(msg.sender, 0);
		emit Deal(true, playerCards[0]);
		houseCards[0] = SbBlackJackDeck.deal(msg.sender, 1);
		emit Deal(false, houseCards[0]);
		playerCards[1] = SbBlackJackDeck.deal(msg.sender, 2);
		emit Deal(true, playerCards[1]);

		games[msg.sender] = Game({
			player: msg.sender,
			bet: msg.value,
			houseCards: houseCards,
			playerCards: playerCards,
			state: GameState.Ongoing,
			cardsDealt: 3
		});

		checkGameResult(games[msg.sender], false);
	}

	function hit() public gameIsGoingOn {
		uint8 nextCard = games[msg.sender].cardsDealt;
		games[msg.sender].playerCards.push(SbBlackJackDeck.deal(msg.sender, nextCard));
		games[msg.sender].cardsDealt = nextCard + 1;
		emit Deal(true, games[msg.sender].playerCards[games[msg.sender].playerCards.length - 1]);
		checkGameResult(games[msg.sender], false);
	}

	function stand() public gameIsGoingOn {

		(uint8 houseScore, uint8 houseScoreBig) = calculateScore(games[msg.sender].houseCards);

		while (houseScoreBig < 17) {
			uint8 nextCard = games[msg.sender].cardsDealt;
			uint8 newCard = SbBlackJackDeck.deal(msg.sender, nextCard);
			games[msg.sender].houseCards.push(newCard);
			games[msg.sender].cardsDealt = nextCard + 1;
			houseScoreBig += SbBlackJackDeck.valueOf(newCard, true);
			emit Deal(false, newCard);
		}

		checkGameResult(games[msg.sender], true);
	}

	function checkGameResult(Game memory game, bool finishGame) private {
		(uint8 houseScore, uint8 houseScoreBig) = calculateScore(game.houseCards);
		(uint8 playerScore, uint8 playerScoreBig) = calculateScore(game.playerCards);

		emit GameStatus(houseScore, houseScoreBig, playerScore, playerScoreBig);

		if (houseScoreBig == BLACKJACK || houseScore == BLACKJACK) {
			if (playerScore == BLACKJACK || playerScoreBig == BLACKJACK) {
				if (!payable(msg.sender).send(game.bet)) revert();
				games[msg.sender].state = GameState.Tie;
				return;
			} else {
				games[msg.sender].state = GameState.House;
				return;
			}
		} else {
			if (playerScore == BLACKJACK || playerScoreBig == BLACKJACK) {
				if (game.playerCards.length == 2 && (SbBlackJackDeck.isTen(game.playerCards[0]) || SbBlackJackDeck.isTen(game.playerCards[1]))) {
					if (!payable(msg.sender).send((game.bet * 5) / 2)) revert();
				} else {
					if (!payable(msg.sender).send(game.bet * 2)) revert();
				}
				games[msg.sender].state = GameState.Player;
				return;
			} else {

				if (playerScore > BLACKJACK) {
					emit Log(1);
					games[msg.sender].state = GameState.House;
					return;
				}

				if (!finishGame) {
					return;
				}

				uint8 playerShortage = 0;
				uint8 houseShortage = 0;

				if (playerScoreBig > BLACKJACK) {
					if (playerScore > BLACKJACK) {
						games[msg.sender].state = GameState.House;
						return;
					} else {
						playerShortage = BLACKJACK - playerScore;
					}
				} else {
					playerShortage = BLACKJACK - playerScoreBig;
				}

				if (houseScoreBig > BLACKJACK) {
					if (houseScore > BLACKJACK) {
						if (!payable(msg.sender).send(game.bet * 2)) revert();
						games[msg.sender].state = GameState.Player;
						return;
					} else {
						houseShortage = BLACKJACK - houseScore;
					}
				} else {
					houseShortage = BLACKJACK - houseScoreBig;
				}

				if (houseShortage == playerShortage) {
					if (!payable(msg.sender).send(game.bet)) revert();
					games[msg.sender].state = GameState.Tie;
				} else if (houseShortage > playerShortage) {
					if (!payable(msg.sender).send(game.bet * 2)) revert();
					games[msg.sender].state = GameState.Player;
				} else {
					games[msg.sender].state = GameState.House;
				}
			}
		}
	}

	function calculateScore(uint8[] memory cards) private pure returns (uint8, uint8) {
		uint8 score = 0;
		uint8 scoreBig = 0;
		bool bigAceUsed = false;
		for (uint i = 0; i < cards.length; ++i) {
			uint8 card = cards[i];
			if (SbBlackJackDeck.isAce(card) && !bigAceUsed) {
				scoreBig += SbBlackJackDeck.valueOf(card, true);
				bigAceUsed = true;
			} else {
				scoreBig += SbBlackJackDeck.valueOf(card, false);
			}
			score += SbBlackJackDeck.valueOf(card, false);
		}
		return (score, scoreBig);
	}

	function getPlayerCard(uint8 id) public view gameIsGoingOn returns(uint8) {
		if (id < 0 || id > games[msg.sender].playerCards.length) {
			revert();
		}
		return games[msg.sender].playerCards[id];
	}

	function getHouseCard(uint8 id) public view gameIsGoingOn returns(uint8) {
		if (id < 0 || id > games[msg.sender].houseCards.length) {
			revert();
		}
		return games[msg.sender].houseCards[id];
	}

	function getPlayerCardsNumber() public view gameIsGoingOn returns(uint) {
		return games[msg.sender].playerCards.length;
	}

	function getHouseCardsNumber() public view gameIsGoingOn returns(uint) {
		return games[msg.sender].houseCards.length;
	}

	function getGameState() public view returns (uint8) {
		if (games[msg.sender].player == address(0)) {
			revert();
		}

		Game storage game = games[msg.sender];

		if (game.state == GameState.Player) {
			return 1;
		}
		if (game.state == GameState.House) {
			return 2;
		}
		if (game.state == GameState.Tie) {
			return 3;
		}

		return 0;
	}

}
