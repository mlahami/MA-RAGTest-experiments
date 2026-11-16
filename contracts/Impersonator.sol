// Benchmark candidate extracted from Ethernaut: ethernaut/contracts/src/levels/Impersonator.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Impersonator is Ownable(msg.sender) {
    uint256 public lockCounter;
    ImpersonatorECLocker[] public lockers;

    event NewLock(address indexed lockAddress, uint256 lockId, uint256 timestamp, bytes signature);

    constructor(uint256 _lockCounter) {
        lockCounter = _lockCounter;
    }

    function deployNewLock(bytes memory signature) public onlyOwner {
        ImpersonatorECLocker newLock = new ImpersonatorECLocker(++lockCounter, signature);
        lockers.push(newLock);
        emit NewLock(address(newLock), lockCounter, block.timestamp, signature);
    }
}

contract ImpersonatorECLocker {
    uint256 public immutable lockId;
    bytes32 public immutable msgHash;
    address public controller;
    mapping(bytes32 => bool) public usedSignatures;

    event LockInitializated(address indexed initialController, uint256 timestamp);
    event Open(address indexed opener, uint256 timestamp);
    event ControllerChanged(address indexed newController, uint256 timestamp);

    error InvalidController();
    error SignatureAlreadyUsed();

    constructor(uint256 _lockId, bytes memory _signature) {
        lockId = _lockId;

        bytes32 _msgHash;
        assembly {
            mstore(0x00, "\x19Ethereum Signed Message:\n32")
            mstore(0x1C, _lockId)
            _msgHash := keccak256(0x00, 0x3c)
        }
        msgHash = _msgHash;

        address initialController = address(1);
        assembly {
            let ptr := mload(0x40)
            mstore(ptr, _msgHash)
            mstore(add(ptr, 32), mload(add(_signature, 0x60)))
            mstore(add(ptr, 64), mload(add(_signature, 0x20)))
            mstore(add(ptr, 96), mload(add(_signature, 0x40)))
            pop(
                staticcall(
                    gas(),
                    initialController,
                    ptr,
                    0x80,
                    0x00,
                    0x20
                )
            )
            if iszero(returndatasize()) {
                mstore(0x00, 0x8baa579f)
                revert(0x1c, 0x04)
            }
            initialController := mload(0x00)
            mstore(0x40, add(ptr, 128))
        }

        usedSignatures[keccak256(_signature)] = true;

        controller = initialController;

        emit LockInitializated(initialController, block.timestamp);
    }

    function open(uint8 v, bytes32 r, bytes32 s) external {
        address add = _isValidSignature(v, r, s);
        emit Open(add, block.timestamp);
    }

    function changeController(uint8 v, bytes32 r, bytes32 s, address newController) external {
        _isValidSignature(v, r, s);
        controller = newController;
        emit ControllerChanged(newController, block.timestamp);
    }

    function _isValidSignature(uint8 v, bytes32 r, bytes32 s) internal returns (address) {
        address _address = ecrecover(msgHash, v, r, s);
        if (_address != controller) revert InvalidController();

        bytes32 signatureHash = keccak256(abi.encode([uint256(r), uint256(s), uint256(v)]));
        if (usedSignatures[signatureHash]) revert SignatureAlreadyUsed();

        usedSignatures[signatureHash] = true;

        return _address;
    }
}
