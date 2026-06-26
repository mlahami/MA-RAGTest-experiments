// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SupplyChain
 * @dev Gère le suivi des colis à travers différentes étapes de transport.
 */
contract SupplyChain {
    
    enum Step { CREATED, IN_TRANSIT, ARRIVED, DELIVERED }

    struct TrackingStep {
        Step status;
        string location;
        uint256 timestamp;
        address updatedBy;
    }

    struct Package {
        uint256 id;
        string description;
        address manufacturer;
        Step currentStatus;
        TrackingStep[] history;
    }

    uint256 public packageCount;
    mapping(uint256 => Package) public packages;
    mapping(address => bool) public authorizedCarriers;

    address public owner;

    event PackageCreated(uint256 indexed packageId, string description);
    event StepUpdated(uint256 indexed packageId, Step status, string location);

    modifier onlyOwner() {
        require(msg.sender == owner, "SupplyChain: Reserve a l'admin");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedCarriers[msg.sender] || msg.sender == owner, "SupplyChain: Non autorise");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @dev Autorise un transporteur à mettre à jour les étapes.
     */
    function authorizeCarrier(address _carrier) external onlyOwner {
        authorizedCarriers[_carrier] = true;
    }

    /**
     * @dev Crée un nouveau colis dans le système.
     */
    function createPackage(string memory _description, string memory _initialLocation) external onlyAuthorized {
        uint256 packageId = packageCount++;
        Package storage p = packages[packageId];
        p.id = packageId;
        p.description = _description;
        p.manufacturer = msg.sender;
        p.currentStatus = Step.CREATED;

        _updateHistory(packageId, Step.CREATED, _initialLocation);
        
        emit PackageCreated(packageId, _description);
    }

    /**
     * @dev Met à jour l'étape de transport d'un colis.
     */
    function updateStep(uint256 _packageId, Step _status, string memory _location) external onlyAuthorized {
        Package storage p = packages[_packageId];
        require(_status > p.currentStatus, "SupplyChain: Impossible de revenir en arriere");
        
        p.currentStatus = _status;
        _updateHistory(_packageId, _status, _location);

        emit StepUpdated(_packageId, _status, _location);
    }

    /**
     * @dev Fonction interne pour enregistrer l'historique.
     */
    function _updateHistory(uint256 _packageId, Step _status, string memory _location) internal {
        packages[_packageId].history.push(TrackingStep({
            status: _status,
            location: _location,
            timestamp: block.timestamp,
            updatedBy: msg.sender
        }));
    }

    /**
     * @dev Récupère l'historique complet d'un colis.
     */
    function getPackageHistory(uint256 _packageId) external view returns (TrackingStep[] memory) {
        return packages[_packageId].history;
    }
}