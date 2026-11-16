// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x96edbe868531bd23a6c05e9d0c424ea64fb1b78b.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbPennyByPenny
{
    struct Holder
    {
        uint unlockTime;
        uint balance;
    }

    mapping (address => Holder) public Acc;

    uint public MinSum;

    SbPennyByPennyLogFile Log;

    bool intitalized;

    function SetMinSum(uint _val)
    public
    {
        if(intitalized)revert();
        MinSum = _val;
    }

    function SetLogFile(address _log)
    public
    {
        if(intitalized)revert();
        Log = SbPennyByPennyLogFile(_log);
    }

    function Initialized()
    public
    {
        intitalized = true;
    }

    function Put(uint _lockTime)
    public
    payable
    {
        Holder storage acc = Acc[msg.sender];
        acc.balance += msg.value;
        if(block.timestamp+_lockTime>acc.unlockTime)acc.unlockTime=block.timestamp+_lockTime;
        Log.AddMessage(msg.sender,msg.value,"Put");
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
                Log.AddMessage(msg.sender,_am,"Collect");
            }
        }
    }

    fallback()
    external
    payable
    {
        Put(0);
    }

}


contract SbPennyByPennyLogFile
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
