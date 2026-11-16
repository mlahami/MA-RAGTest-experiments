// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x01f8c4e3fa3edeb29e514cba738d87ce8c091d3f.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbPersonalBank
{
    mapping (address=>uint256) public balances;

    uint public MinSum = 1 ether;

    SbPersonalBankLogFile Log = new SbPersonalBankLogFile();

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
        Log = SbPersonalBankLogFile(_log);
    }

    function Initialized()
    public
    {
        intitalized = true;
    }

    function Deposit()
    public
    payable
    {
        balances[msg.sender]+= msg.value;
        Log.AddMessage(msg.sender,msg.value,"Put");
    }

    function Collect(uint _am)
    public
    payable
    {
        if(balances[msg.sender]>=MinSum && balances[msg.sender]>=_am)
        {
            (bool success, ) = msg.sender.call{value: _am}("");
            if(success)
            {
                unchecked { balances[msg.sender]-=_am; }
                Log.AddMessage(msg.sender,_am,"Collect");
            }
        }
    }

    fallback()
    external
    payable
    {
        Deposit();
    }

}



contract SbPersonalBankLogFile
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
