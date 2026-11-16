// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x4e73b32ed6c35f570686b89848e5f39f20ecc106.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbPrivateEthCell
{
    mapping (address=>uint256) public balances;

    uint public MinSum;

    SbPrivateEthCellLogFile Log;

    bool intitalized;

    function SetMinSum(uint _val)
    public
    {
        require(!intitalized);
        MinSum = _val;
    }

    function SetLogFile(address _log)
    public
    {
        require(!intitalized);
        Log = SbPrivateEthCellLogFile(_log);
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



contract SbPrivateEthCellLogFile
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
