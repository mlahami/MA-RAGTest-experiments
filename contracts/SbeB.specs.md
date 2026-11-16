User Story: Gas Cost Reimbursement Vault

Title: Reimburse Gas Consumed by Authorized Callers from a Funded Vault

As the operator of a relaying service
I want authorized callers to be reimbursed in wei for the gas consumed since they measured a starting gas value
So that relayers who forward calls are compensated from a funded vault

Acceptance Criteria
1. Deploy and Fund
Given a deployer
When SbeB is deployed
Then the deployer should be marked as authorized
And the contract should accept plain Ether transfers to build its reimbursement balance
2. Manage Authorizations
Given I am authorized
When I call setAuth with an address and a boolean
Then authorized[address] should be set to that boolean
And an unauthorized caller should be rejected with "not authorized"
3. Request a Reimbursement
Given I am authorized and the vault holds enough Ether
When I call g with a receiver address and a gasStart value
Then the contract should compute gasUsed as gasStart minus the gas left at that point
And it should send gasUsed wei to the receiver
And a Log event should be emitted with gasUsed
And an unauthorized caller should be rejected with "not authorized"
4. Failed Reimbursement
Given the payment to the receiver fails, for example because the balance is insufficient or the receiver rejects Ether
When g is called
Then the call should revert with "send failed"
5. Invalid Start Value
Given gasStart is lower than the gas remaining when g measures it
When g is called
Then the call should revert

Notes
The intended caller is a contract that reads gasleft() and immediately calls g with that value; tests may use a small helper contract for this or pass gasStart directly
gasUsed is paid at a rate of one wei per unit of gas
Authorization is a flat flag; any authorized address may authorize or de-authorize any address, including itself
