User Story: Upgradeable Proxy Administration

Title: Manage the Admin and Implementation of Upgradeable Proxies Through an Owner-Controlled Admin Contract

As the owner of an upgradeable application
I want a dedicated admin contract that can read and change a proxy's admin and implementation
So that upgrades are performed only by me while ordinary users keep interacting with the application

Acceptance Criteria
1. Deploy the Admin
Given a deployer
When ProxyAdmin is deployed
Then the deployer should be recorded as owner
2. Read the Proxy Admin
Given a proxy whose admin is this ProxyAdmin
When anyone calls getProxyAdmin with the proxy address
Then it should return the proxy's admin address
And it should revert with "call failed" if the proxy call fails
3. Read the Proxy Implementation
Given a proxy whose admin is this ProxyAdmin
When anyone calls getProxyImplementation with the proxy address
Then it should return the proxy's current implementation address
And it should revert with "call failed" if the proxy call fails
4. Upgrade a Proxy
Given I am the owner and this ProxyAdmin is the proxy's admin
When I call upgrade with the proxy and a new implementation address
Then the proxy implementation should be updated
And the call should revert with "not owner" if I am not the owner
And it should revert with "implementation is not a contract" if the address has no code
5. Change a Proxy's Admin
Given I am the owner and this ProxyAdmin is the proxy's admin
When I call changeProxyAdmin with the proxy and a new admin address
Then the proxy admin should be updated to the new address
And the call should revert with "not owner" if I am not the owner
And it should revert with "admin = zero address" if the new admin is the zero address

Notes
The file also contains the helper contract Proxy (EIP-1967 storage slots, admin set to its deployer) and the StorageSlot library; tests deploy a Proxy, hand its admin role to ProxyAdmin with changeAdmin, and use the implementation contracts ProxyAdminCounterV1 and ProxyAdminCounterV2 (a counter with inc, and a counter with inc and dec) as the initial and upgraded implementations
On the Proxy, admin functions run only for the admin; calls from any other address are forwarded to the implementation
The ProxyAdmin owner is fixed at deployment
