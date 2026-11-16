// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0xec329ffc97d75fe03428ae155fc7793431487f63.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbTokenSenderOwned {
    constructor() {
        owner = msg.sender;
    }

    address public owner;

    modifier onlyOwner { if (msg.sender == owner) _; }

    function changeOwner(address _newOwner) public onlyOwner {
        owner = _newOwner;
    }

    function execute(address _dst, uint _value, bytes memory _data) public onlyOwner {
        _dst.call{value: _value}(_data);
    }
}

interface SbTokenSenderIToken {
    function transfer(address, uint) external returns(bool);
    function balanceOf(address) external view returns (uint);
}

contract SbTokenSenderToken is SbTokenSenderIToken {
    mapping(address => uint) public balances;

    constructor(uint initialSupply) {
        balances[msg.sender] = initialSupply;
    }

    function transfer(address to, uint amount) external returns(bool) {
        if (balances[msg.sender] < amount) return false;
        balances[msg.sender] -= amount;
        balances[to] += amount;
        return true;
    }

    function balanceOf(address who) external view returns (uint) {
        return balances[who];
    }
}

contract SbTokenSender is SbTokenSenderOwned {
    SbTokenSenderIToken public token;
    uint public totalToDistribute;

    uint public next;

    struct Transfer {
        address addr;
        uint amount;
    }

    Transfer[] public transfers;

    constructor(address _token) {
        token = SbTokenSenderIToken(_token);
    }

    uint constant D160 = 0x0010000000000000000000000000000000000000000;

    function fill(uint[] memory data) public onlyOwner {

        if (next>0) revert();

        uint acc;
        uint offset = transfers.length;
        for (uint j = 0; j < data.length; j++) transfers.push();
        for (uint i = 0; i < data.length; i++ ) {
            address addr = address(uint160( data[i] & (D160-1) ));
            uint amount = data[i] / D160;

            transfers[offset + i].addr = addr;
            transfers[offset + i].amount = amount;
            acc += amount;
        }
        totalToDistribute += acc;
    }

    function run() public onlyOwner {
        if (transfers.length == 0) return;

        uint mNext = next;

        next = transfers.length;

        if ((mNext == 0 ) && ( token.balanceOf(address(this)) != totalToDistribute)) revert();

        while ((mNext<transfers.length) && ( gas() > 150000 )) {
            uint amount = transfers[mNext].amount;
            address addr = transfers[mNext].addr;
            if (amount > 0) {
                if (!token.transfer(addr, transfers[mNext].amount)) revert();
            }
            mNext ++;
        }

        next = mNext;
    }

    function hasTerminated() public view returns (bool) {
        if (transfers.length == 0) return false;
        if (next < transfers.length) return false;
        return true;
    }

    function nTransfers() public view returns (uint) {
        return transfers.length;
    }

    function gas() internal view returns (uint _gas) {
        assembly {
            _gas:= gas()
        }
    }

}
