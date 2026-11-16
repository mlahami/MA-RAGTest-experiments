User Story: Generic Deployer and Call Forwarder

Title: Deploy Arbitrary Contracts from Bytecode and Forward Arbitrary Calls

As a developer
I want a single contract that can deploy any contract from its creation bytecode and call any target with any data
So that I can create and operate contracts through one address

Acceptance Criteria
1. Receive Ether
Given anyone holds Ether
When they send Ether directly to SbeProxy
Then the Ether should be accepted
2. Deploy a Contract
Given valid contract creation bytecode
When I call deploy with the bytecode, optionally sending Ether
Then a new contract should be created by SbeProxy with the sent Ether as its initial balance
And the new contract address should be returned
And a Deploy event should be emitted with the new address
And the call should revert with "deploy failed" if creation fails, for example with invalid bytecode or a reverting constructor
3. Execute a Call
Given a target address and call data
When I call execute, optionally sending Ether
Then the target should be called with the data and the sent Ether
And the call should revert with "failed" if the target call fails
4. Deployer Identity
Given a contract deployed through deploy that records its deployer
When it is inspected
Then SbeProxy should appear as its deployer (msg.sender at construction)
And calls made through execute should reach the target with SbeProxy as msg.sender

Notes
There is no access control: any caller may deploy or execute
SbeProxy stores no state about deployed contracts; their addresses are available from the return value and the Deploy event
The value forwarded by execute is exactly msg.value
