// Benchmark candidate extracted from DeFiVulnLabs: DeFiVulnLabs/src/test/phantom-permit.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract VulnPermit {
    IERC20 public token;
    constructor(IERC20 _token) {
        token = _token;
    }
    function deposit(uint256 amount) public {
        require(
            token.transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
    }
    function depositWithPermit(
        address target,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) public {
        (bool success, ) = address(token).call(
            abi.encodeWithSignature(
                "permit(address,uint256,uint8,bytes32,bytes32)",
                target,
                amount,
                v,
                r,
                s
            )
        );
        require(success, "Permit failed");
        require(
            token.transferFrom(target, address(this), amount),
            "Transfer failed"
        );
    }
    function withdraw(uint256 amount) public {
        require(token.transfer(msg.sender, amount), "Transfer failed");
    }
}
contract VulnPermitMockToken is ERC20 {
    uint8 private immutable _dec;
    constructor(string memory name_, string memory symbol_, uint8 decimals_) ERC20(name_, symbol_) { _dec = decimals_; }
    function decimals() public view override returns (uint8) { return _dec; }
    function mint(address to, uint256 amount) external { _mint(to, amount); }
}
