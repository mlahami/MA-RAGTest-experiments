// Benchmark candidate ported from smartbugs-curated: dataset/reentrancy/0x627fa62ccbb1c1b04ffaecd72a53e37fc0e17839.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract SbTokenBankOwnable
{
    address newOwner;
    address owner = msg.sender;

    function changeOwner(address addr)
    public
    onlyOwner
    {
        newOwner = addr;
    }

    function confirmOwner()
    public
    {
        if(msg.sender==newOwner)
        {
            owner=newOwner;
        }
    }

    modifier onlyOwner
    {
        if(owner == msg.sender)_;
    }
}

contract SbTokenBankToken is SbTokenBankOwnable
{
    address tokenOwner = msg.sender;
    function WithdrawToken(address token, uint256 amount,address to)
    public
    onlyOwner
    {
        token.call(abi.encodeWithSelector(bytes4(keccak256("transfer(address,uint256)")),to,amount));
    }
}

contract SbTokenBank is SbTokenBankToken
{
    uint public MinDeposit;
    mapping (address => uint) public Holders;

    function initTokenBank()
    public
    {
        tokenOwner = msg.sender;
        MinDeposit = 1 ether;
    }

    receive()
    external
    payable
    {
        Deposit();
    }

    function Deposit()
    public
    payable
    {
        if(msg.value>MinDeposit)
        {
            Holders[msg.sender]+=msg.value;
        }
    }

    function WitdrawTokenToHolder(address _to,address _token,uint _amount)
    public
    onlyOwner
    {
        if(Holders[_to]>0)
        {
            Holders[_to]=0;
            WithdrawToken(_token,_amount,_to);
        }
    }

    function WithdrawToHolder(address _addr, uint _wei)
    public
    onlyOwner
    payable
    {
        if(Holders[_addr]>0)
        {
            (bool success, ) = _addr.call{value: _wei}("");
            if(success)
            {
                unchecked { Holders[_addr]-=_wei; }
            }
        }
    }
}
