// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/king_of_the_ether_throne.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbKingOfTheEtherThrone {

    struct Monarch {
        address etherAddress;
        string name;
        uint claimPrice;
        uint coronationTimestamp;
    }

    address wizardAddress;

    modifier onlywizard { if (msg.sender == wizardAddress) _; }

    uint constant startingClaimPrice = 0.1 ether;

    uint constant claimPriceAdjustNum = 3;
    uint constant claimPriceAdjustDen = 2;

    uint constant wizardCommissionFractionNum = 1;
    uint constant wizardCommissionFractionDen = 100;

    uint public currentClaimPrice;

    Monarch public currentMonarch;

    Monarch[] public pastMonarchs;

    constructor() {
        wizardAddress = msg.sender;
        currentClaimPrice = startingClaimPrice;
        currentMonarch = Monarch(
            wizardAddress,
            "[Vacant]",
            0,
            block.timestamp
        );
    }

    function numberOfMonarchs() public view returns (uint n) {
        return pastMonarchs.length;
    }

    event ThroneClaimed(
        address usurperEtherAddress,
        string usurperName,
        uint newClaimPrice
    );

    fallback() external payable {
        claimThrone(string(msg.data));
    }

    function claimThrone(string memory name) public payable {

        uint valuePaid = msg.value;

        if (valuePaid < currentClaimPrice) {
            payable(msg.sender).send(valuePaid);
            return;
        }

        if (valuePaid > currentClaimPrice) {
            uint excessPaid = valuePaid - currentClaimPrice;
            payable(msg.sender).send(excessPaid);
            valuePaid = valuePaid - excessPaid;
        }

        uint wizardCommission = (valuePaid * wizardCommissionFractionNum) / wizardCommissionFractionDen;

        uint compensation = valuePaid - wizardCommission;

        if (currentMonarch.etherAddress != wizardAddress) {
            payable(currentMonarch.etherAddress).send(compensation);
        } else {
        }

        pastMonarchs.push(currentMonarch);
        currentMonarch = Monarch(
            msg.sender,
            name,
            valuePaid,
            block.timestamp
        );

        uint rawNewClaimPrice = currentClaimPrice * claimPriceAdjustNum / claimPriceAdjustDen;
        if (rawNewClaimPrice < 0.01 ether) {
            currentClaimPrice = rawNewClaimPrice;
        } else if (rawNewClaimPrice < 0.1 ether) {
            currentClaimPrice = 0.0001 ether * (rawNewClaimPrice / 0.0001 ether);
        } else if (rawNewClaimPrice < 1 ether) {
            currentClaimPrice = 0.001 ether * (rawNewClaimPrice / 0.001 ether);
        } else if (rawNewClaimPrice < 10 ether) {
            currentClaimPrice = 0.01 ether * (rawNewClaimPrice / 0.01 ether);
        } else if (rawNewClaimPrice < 100 ether) {
            currentClaimPrice = 0.1 ether * (rawNewClaimPrice / 0.1 ether);
        } else if (rawNewClaimPrice < 1000 ether) {
            currentClaimPrice = 1 ether * (rawNewClaimPrice / 1 ether);
        } else if (rawNewClaimPrice < 10000 ether) {
            currentClaimPrice = 10 ether * (rawNewClaimPrice / 10 ether);
        } else {
            currentClaimPrice = rawNewClaimPrice;
        }

        emit ThroneClaimed(currentMonarch.etherAddress, currentMonarch.name, currentClaimPrice);
    }

    function sweepCommission(uint amount) public onlywizard {
        payable(wizardAddress).send(amount);
    }

    function transferOwnership(address newOwner) public onlywizard {
        wizardAddress = newOwner;
    }

}
