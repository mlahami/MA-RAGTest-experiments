User Story: Fibonacci-Based Ether Withdrawal

Title: Withdraw Ether Amounts That Follow a Fibonacci-Like Sequence

As a participant in a funded withdrawal scheme
I want each successive withdrawal to pay out the next number of a Fibonacci-like sequence in Ether
So that payouts follow a transparent, predictable mathematical rule computed by a shared calculation library

Acceptance Criteria
1. Deploy and Fund the Contract
Given a deployed SbFibonacciBalanceLib calculation contract
When the SbFibonacciBalance contract is deployed with the library address and an initial Ether amount
Then the library address should be stored and readable through fibonacciLibrary
And the starting sequence value start should be 3
And withdrawalCounter and calculatedFibNumber should both be 0
And the contract should hold the Ether sent at deployment
2. Withdraw the Next Fibonacci Amount
Given the contract holds enough Ether
When any user calls withdraw
Then withdrawalCounter should increase by 1
And calculatedFibNumber should be set to the Fibonacci-like number for the new counter, using start as the zeroth value and start + 1 as the first value
And the caller should receive calculatedFibNumber Ether
And the transaction should revert if the library calculation fails or the contract balance is insufficient
3. Sequence Rule
Given the sequence starts at start = 3
When the n-th withdrawal is computed
Then the value for n = 0 is 3, for n = 1 is 4, and every later value is the sum of the two previous ones (for example n = 2 gives 7)
4. Use Library Helper Functions
Given a user needs to call a calculation function of the library through the main contract
When the user sends a call that does not match a function of SbFibonacciBalance
Then the call should be forwarded to the library and executed on behalf of the contract
And the transaction should revert if the forwarded call fails
And plain Ether transfers without data should be rejected
5. Protect Contract Configuration
Given the contract has been deployed
When any forwarded library call is executed
Then the stored fibonacciLibrary address must not change
And the starting value and withdrawal counter must only change according to the rules above
And no user should be able to obtain more Ether than the sequence value of the current withdrawal

Notes
The library contract SbFibonacciBalanceLib exposes setStart, setFibonacci and the public values start and calculatedFibNumber
The library must be deployed first and its address passed to the constructor
Withdrawals are open to any address; the amount depends only on how many withdrawals happened before
The contract does not accept plain Ether deposits after deployment
