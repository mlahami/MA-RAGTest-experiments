User Story: Self-Controlled Switch

Title: Operate an On/Off Switch Only Through the Controlled Entry Point

As a user of the Switch contract
I want to submit switch commands through a single controlled entry point
So that the switch state can only be changed by the contract itself and only with the permitted command

Acceptance Criteria
1. Initial State
Given the Switch contract is deployed
When I query switchOn
Then it should be false
And offSelector should equal the selector of turnSwitchOff()
2. Restrict Direct Switching
Given I am an external account or another contract
When I call turnSwitchOn or turnSwitchOff directly
Then the transaction should revert with "Only the contract can call this"
And switchOn should not change
3. Turn the Switch Off Through flipSwitch
Given I build _data as the ABI-encoded call to turnSwitchOff()
When I call flipSwitch with that _data using standard ABI encoding
Then the contract should call itself with _data
And switchOn should be false afterwards
4. Reject Other Commands
Given the _data I submit is not the turnSwitchOff() call
When I call flipSwitch
Then the transaction should revert with "Can only call the turnOffSwitch function"
And switchOn should not change
5. Propagate Failures of the Inner Call
Given flipSwitch accepts my command
When the internal call to the contract fails
Then the transaction should revert with "call failed :("
6. Read the State
Given any account
When I query switchOn and offSelector
Then I should receive the current values
Notes
The only command an external user is meant to run through flipSwitch is turnSwitchOff
turnSwitchOn and turnSwitchOff are guarded by the onlyThis modifier
No events are emitted
