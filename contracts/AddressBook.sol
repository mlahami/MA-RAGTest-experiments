// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title AddressBook
 * @dev Permet à chaque adresse de gérer sa propre liste de contacts personnels.
 */
contract AddressBook {

    struct Contact {
        string name;
        address contactAddress;
        bool exists;
    }

    // Mapping: Adresse du propriétaire => (Nom unique => Détails du contact)
    mapping(address => mapping(string => Contact)) private userContacts;
    
    // Liste des noms pour permettre l'énumération (optionnel selon le gaz)
    mapping(address => string[]) private contactNames;

    event ContactAdded(address indexed owner, string name, address contactAddress);
    event ContactRemoved(address indexed owner, string name);

    /**
     * @dev Ajoute ou met à jour un contact dans le répertoire de l'appelant.
     * @param _name Le nom identifiant le contact.
     * @param _contactAddress L'adresse blockchain du contact.
     */
    function addContact(string memory _name, address _contactAddress) public {
        if (!userContacts[msg.sender][_name].exists) {
            contactNames[msg.sender].push(_name);
        }
        
        userContacts[msg.sender][_name] = Contact(_name, _contactAddress, true);
        emit ContactAdded(msg.sender, _name, _contactAddress);
    }

    /**
     * @dev Récupère l'adresse d'un contact par son nom.
     * @param _name Le nom du contact à rechercher.
     */
    function getContact(string memory _name) public view returns (address) {
        require(userContacts[msg.sender][_name].exists, "Contact introuvable.");
        return userContacts[msg.sender][_name].contactAddress;
    }

    /**
     * @dev Retourne tous les noms de contacts enregistrés par l'appelant.
     */
    function getAllContactNames() public view returns (string[] memory) {
        return contactNames[msg.sender];
    }

    /**
     * @dev Supprime un contact du répertoire.
     * @param _name Le nom du contact à supprimer.
     */
    function removeContact(string memory _name) public {
        require(userContacts[msg.sender][_name].exists, "Contact n'existe pas.");
        delete userContacts[msg.sender][_name];
        emit ContactRemoved(msg.sender, _name);
    }
}