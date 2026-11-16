// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x23a91059fdc9579a9fbd0edc5f2ea0bfdb70deb4.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbPrivateBank
{
    mapping (address => uint) public balances;

    uint public MinDeposit = 1 ether;

    SbPrivateBankLog TransferLog;

    constructor(address _log)
    {
        TransferLog = SbPrivateBankLog(_log);
    }

    function Deposit()
    public
    payable
    {
        if(msg.value >= MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
        }
    }

    function CashOut(uint _am)
    public
    {
        if(_am<=balances[msg.sender])
        {
            (bool success, ) = msg.sender.call{value: _am}("");
            if(success)
            {
                unchecked { balances[msg.sender]-=_am; }
                TransferLog.AddMessage(msg.sender,_am,"CashOut");
            }
        }
    }

    receive() external payable{}

}

contract SbPrivateBankLog
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
