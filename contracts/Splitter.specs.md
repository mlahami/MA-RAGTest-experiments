User Story: Automatic Ether Revenue Splitter

Title: Split Incoming Ether Equally Between Three Beneficiaries

As a sender of Ether
I want to send funds to a contract that automatically distributes them to three predefined recipients
So that payments are transparently and instantly shared without manual intervention

Acceptance Criteria
1. Define Beneficiaries
Given the contract is deployed
When three valid addresses are provided
Then those addresses should be stored as beneficiaries
And zero addresses should not be accepted
2. Receive Ether
Given the contract is active
When it receives any non-zero Ether amount
Then the split process should be triggered automatically
And if zero Ether is sent, the transaction should fail
3. Split Funds Equally
Given Ether is received
When the split function executes
Then the value should be divided equally into three parts
And each beneficiary should receive their share
And all transfers must succeed or the transaction should revert
4. Emit Payment Event
Given a successful split occurs
When funds are distributed
Then a PaymentSplit event should be emitted containing:
Sender address
Total amount received
Amount per beneficiary
5. Handle Remainder Safely
Given the Ether amount is not divisible by 3
When the split occurs
Then the leftover wei should remain in the contract or be managed explicitly
And it should not be lost or misallocated
6. Check Contract Balance
Given I want to verify contract state
When I query the balance
Then I should see the remaining Ether stored in the contract
Notes
The contract enforces equal distribution among exactly three fixed recipients
Uses low-level calls for ETH transfer (requires careful security consideration)
There is no access control; anyone can send Ether
Remainders from division may accumulate in the contract
This pattern is useful for payroll, revenue sharing, or affiliate payouts