// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0xb620cee6b52f96f3c6b253e6eea556aa2d214a99.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbDrainMe {

address public winner = address(0);
address public owner;
address public firstTarget;
address public secondTarget;
address[] public players;

mapping(address=>bool) approvedPlayers;

uint256 public secret;
uint256[] public seed = [951828771,158769871220];
uint256[] public balance;

constructor(address _firstTarget, address _secondTarget) {
	firstTarget = _firstTarget;
	secondTarget = _secondTarget;
}

function DranMe() public payable{
	owner = msg.sender;
}

modifier onlyOwner() {
    require(msg.sender == owner);
    _;
}

modifier onlyWinner() {
    require(msg.sender == winner);
    _;
}

modifier onlyPlayers() {
    require(approvedPlayers[msg.sender]);
    _;
}

function getLength() public view returns(uint256) {
	return seed.length;
}

function setSecret(uint256 _secret) public payable onlyOwner{
	secret = _secret;
}

function getPlayerCount() public view returns(uint256) {
	return players.length;
}

function getPrize() public view returns(uint256) {
	return address(this).balance;
}

function becomePlayer() public payable{
	require(msg.value >= 0.02 ether);
	players.push(msg.sender);
	approvedPlayers[msg.sender]=true;
}

function manipulateSecret() public payable onlyPlayers{
	require (msg.value >= 0.01 ether);
	if(msg.sender!=owner || unlockSecret()){
	    uint256 amount = 0;
        payable(msg.sender).transfer(amount);
	}
}

function unlockSecret() private returns(bool){
    bytes32 hash = keccak256(abi.encodePacked(blockhash(block.number-1)));
    uint256 secret = uint256(hash);
        if(secret%5==0){
            winner = msg.sender;
            return true;
        }
        else{
            return false;
        }
    }

function callFirstTarget () public payable onlyPlayers {
	require (msg.value >= 0.005 ether);
	firstTarget.call{value: msg.value}("");
}

function callSecondTarget () public payable onlyPlayers {
	require (msg.value >= 0.005 ether);
	secondTarget.call{value: msg.value}("");
}

function setSeed (uint256 _index, uint256 _value) public payable onlyPlayers {
	seed[_index] = _value;
}

function addSeed (uint256 _add) public payable onlyPlayers {
	while (seed.length < _add) seed.push();
	while (seed.length > _add) seed.pop();
}

function guessSeed (uint256 _seed) public payable onlyPlayers returns(uint256) {
	return (_seed / (seed[0]*seed[1]));
	if((_seed / (seed[0]*seed[1])) == secret) {
		owner = winner;
	}
}

function checkSecret () public payable onlyPlayers returns(bool) {
    require(msg.value >= 0.01 ether);
    if(msg.value == secret){
        return true;
    }
}

function winPrize() public payable onlyOwner {
	owner.call{value: 1 wei}("");
}

function claimPrize() public payable onlyWinner {
	payable(winner).transfer(address(this).balance);
}

receive() external payable{
	}
}
