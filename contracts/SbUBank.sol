// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x7541b76cb60f4c60af330c208b0623b7f54bf615.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbUBank
{
    function Put(uint _unlockTime)
    public
    payable
    {
        Holder storage acc = Acc[msg.sender];
        acc.balance += msg.value;
        acc.unlockTime = _unlockTime>block.timestamp?_unlockTime:block.timestamp;
        LogFile.AddMessage(msg.sender,msg.value,"Put");
    }

    function Collect(uint _am)
    public
    payable
    {
        Holder storage acc = Acc[msg.sender];
        if( acc.balance>=MinSum && acc.balance>=_am && block.timestamp>acc.unlockTime)
        {
            (bool success, ) = msg.sender.call{value: _am}("");
            if(success)
            {
                unchecked { acc.balance-=_am; }
                LogFile.AddMessage(msg.sender,_am,"Collect");
            }
        }
    }

    fallback()
    external
    payable
    {
        Put(0);
    }

    struct Holder
    {
        uint unlockTime;
        uint balance;
    }

    mapping (address => Holder) public Acc;

    SbUBankLog LogFile;

    uint public MinSum = 2 ether;

    constructor(address log) {
        LogFile = SbUBankLog(log);
    }
}


contract SbUBankLog
{
    struct Message
    {
        address Sender;
        string  Data;
        uint Val;
        uint  Time;
    }

    Message[] public History;

    Message LastMsg;

    function AddMessage(address _adr,uint _val,string memory _data)
    public
    {
        LastMsg.Sender = _adr;
        LastMsg.Time = block.timestamp;
        LastMsg.Val = _val;
        LastMsg.Data = _data;
        History.push(LastMsg);
    }
}
