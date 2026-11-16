// Benchmark candidate extracted from Ethernaut: ethernaut/contracts/src/levels/EllipticToken.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract EllipticToken is Ownable(msg.sender), ERC20 {
    error HashAlreadyUsed();
    error InvalidOwner();
    error InvalidReceiver();
    error InvalidSpender();

    constructor() ERC20("EllipticToken", "ETK") {}

    mapping(bytes32 => bool) public usedHashes;

    function redeemVoucher(
        uint256 amount,
        address receiver,
        bytes32 salt,
        bytes memory ownerSignature,
        bytes memory receiverSignature
    ) external {
        bytes32 voucherHash = keccak256(abi.encodePacked(amount, receiver, salt));
        if (usedHashes[voucherHash]) revert HashAlreadyUsed();

        if (ECDSA.recover(voucherHash, ownerSignature) != owner()) revert InvalidOwner();

        if (ECDSA.recover(voucherHash, receiverSignature) != receiver) revert InvalidReceiver();

        usedHashes[voucherHash] = true;

        _mint(receiver, amount);
    }

    function permit(uint256 amount, address spender, bytes memory tokenOwnerSignature, bytes memory spenderSignature)
        external
    {
        bytes32 permitHash = keccak256(abi.encode(amount));
        if (usedHashes[permitHash]) revert HashAlreadyUsed();
        if (usedHashes[bytes32(amount)]) revert HashAlreadyUsed();

        address tokenOwner = ECDSA.recover(bytes32(amount), tokenOwnerSignature);

        bytes32 permitAcceptHash = keccak256(abi.encodePacked(tokenOwner, spender, amount));
        if (ECDSA.recover(permitAcceptHash, spenderSignature) != spender) revert InvalidSpender();

        usedHashes[permitHash] = true;

        _approve(tokenOwner, spender, amount);
    }
}
