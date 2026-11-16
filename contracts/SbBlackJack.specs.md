User Story: On-Chain Blackjack Against the House

Title: Play a Game of Blackjack With an Ether Bet

As a player
I want to place a bet, receive cards, draw more cards and stand against the house
So that I can win twice my bet (or 2.5 times for a natural blackjack) when my hand beats the dealer

Acceptance Criteria
1. Fund the House
Given the SbBlackJack contract is deployed
When anyone sends Ether to the contract without calling a function
Then the Ether should be accepted as house funds
2. Start a Game
Given I have no ongoing game
When I call deal with a bet between minBet (0.05 ETH) and maxBet (5 ETH)
Then I should receive two cards and the house one card, each announced with a Deal event
And my game should be stored with my bet, the cards and the Ongoing state
And a GameStatus event should report both scores
And the call should revert if the bet is out of range or I already have an ongoing game
3. Draw a Card
Given my game is ongoing
When I call hit
Then one more card should be added to my hand and announced with a Deal event
And if my score exceeds 21, the house wins and the game ends
And the call should revert if I have no ongoing game
4. Stand
Given my game is ongoing
When I call stand
Then the house should draw cards until its best score reaches at least 17
And the game should be settled: a tie returns my bet, a win pays twice my bet, and a loss keeps my bet
5. Blackjack Rules
Given cards have values where face cards count 10 and an ace counts 1 or 11
When either side reaches 21
Then the game should finish immediately; a player blackjack pays twice the bet, or 2.5 times for a two-card hand containing a ten
And if both have 21 the bet is returned
And any failed payment must revert the transaction
6. Fair Cards
Given a card is dealt
When the card value is determined
Then the value must not be predictable or chosen by the player before the transaction is sent
7. Query the Game
Given my game is ongoing
When I call getPlayerCard, getHouseCard, getPlayerCardsNumber or getHouseCardsNumber
Then my cards and counts should be returned, reverting for an index out of range or with no ongoing game
And getGameState should return 0 ongoing, 1 player won, 2 house won, 3 tie, reverting if I never played

Notes
The deck draws from 52 card values; card / 4 gives the rank and card % 4 the suit
