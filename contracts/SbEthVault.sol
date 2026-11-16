// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x8c7777c45481dba411450c228cb692ac3d550344.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbEthVault
{
    mapping (address => uint) public balances;

    SbEthVaultLog TransferLog;

    uint public MinDeposit = 1 ether;

    constructor(address _log)
    {
        TransferLog = SbEthVaultLog(_log);
    }

    function Deposit()
    public
    payable
    {
        if(msg.value > MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
        }
    }

    function CashOut(uint _am)
    public
    payable
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

contract SbEthVaultLog
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
