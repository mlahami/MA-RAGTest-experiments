// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Splitter
 * @dev Répartit automatiquement l'Ether reçu entre trois adresses fixes.
 */
contract Splitter {
    address payable[3] public beneficiaries;

    event PaymentSplit(address indexed sender, uint256 totalAmount, uint256 amountPerPerson);

    /**
     * @dev Définit les 3 adresses qui recevront les parts.
     * @param _b1 Première adresse.
     * @param _b2 Deuxième adresse.
     * @param _b3 Troisième adresse.
     */
    constructor(address payable _b1, address payable _b2, address payable _b3) {
        require(_b1 != address(0) && _b2 != address(0) && _b3 != address(0), "Splitter: adresse zero interdite");
        beneficiaries[0] = _b1;
        beneficiaries[1] = _b2;
        beneficiaries[2] = _b3;
    }

    /**
     * @dev Fonction native pour recevoir de l'Ether et le diviser.
     */
    receive() external payable {
        require(msg.value > 0, "Splitter: aucun Ether envoye");
        split();
    }

    /**
     * @dev Divise le montant reçu en 3 parts égales.
     */
    function split() public payable {
        uint256 share = msg.value / 3;
        require(share > 0, "Splitter: montant trop faible pour division");

        for (uint i = 0; i < 3; i++) {
            (bool success, ) = beneficiaries[i].call{value: share}("");
            require(success, "Splitter: echec du transfert");
        }

        emit PaymentSplit(msg.sender, msg.value, share);
        
        // Remarque : Le reste (modulo) de la division reste sur le contrat 
        // ou peut être géré séparément pour éviter de bloquer des wei.
    }

    /**
     * @dev Retourne le solde actuel du contrat (devrait être proche de 0 après split).
     */
    function getContractBalance() public view returns (uint256) {
        return address(this).balance;
    }
}