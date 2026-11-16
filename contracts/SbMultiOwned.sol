// Benchmark candidate ported from smartbugs-curated: dataset/access_control/multiowned_vulnerable.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbMultiOwnedMultiOwnable {
  address public root;
  mapping (address => address) public owners;

  constructor() {
    root = msg.sender;
    owners[root] = root;
  }

  modifier onlyOwner() {
    require(owners[msg.sender] != address(0));
    _;
  }

  function newOwner(address _owner) external returns (bool) {
    require(_owner != address(0));
    owners[_owner] = msg.sender;
    return true;
  }

  function deleteOwner(address _owner) onlyOwner external returns (bool) {
    require(owners[_owner] == msg.sender || (owners[_owner] != address(0) && msg.sender == root));
    owners[_owner] = address(0);
    return true;
  }
}

contract SbMultiOwned is SbMultiOwnedMultiOwnable {

  function withdrawAll() public onlyOwner {
    payable(msg.sender).transfer(address(this).balance);
  }

  receive() external payable {
  }

}
