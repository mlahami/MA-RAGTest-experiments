User Story: Upgradeable Engine Behind a Proxy

Title: Run Engine Logic Through a Proxy With a Single Authorized Upgrader

As the deployer of an upgradeable system
I want the engine logic to be initialized exactly once for my deployment and upgradeable only by the recorded upgrader
So that nobody else can take over or replace the logic

Acceptance Criteria
1. Deploy Through the Proxy
Given a deployed DvlEngine implementation
When DvlEngineMotorbike is deployed with the implementation address
Then the implementation address should be stored in the EIP-1967 implementation slot
And initialize should be executed in the proxy's context
And reading through the proxy should give upgrader equal to the proxy deployer and horsePower equal to 1000
And deploying the proxy with an address without code should revert with "ERC1967: new implementation is not a contract"
2. Initialize Only Once
Given the system is already initialized through the proxy
When anyone calls initialize again through the proxy
Then it should revert with InvalidInitialization
3. Protect the Implementation Contract
Given the implementation contract deployed on its own
When any account calls initialize directly on it
Then that account must not obtain the upgrader role over the logic contract
And no unrelated account should be able to call upgradeToAndCall successfully on the implementation
4. Upgrade the Logic
Given I am the upgrader
When I call upgradeToAndCall(newImplementation, data)
Then the implementation slot should hold newImplementation
And if data is not empty, it should be executed with delegatecall on newImplementation, reverting with "Call failed" if that call fails
And newImplementation without code should be rejected with "ERC1967: new implementation is not a contract"
And any caller other than the upgrader should be rejected with "Can't upgrade"
5. Greet
Given the engine is reachable directly or through the proxy
When anyone calls greetMe
Then a Returny event with value 0x42 (66) should be emitted

Notes
DvlEngineMotorbike is the proxy helper: constructor(logic) only, every other call is forwarded with delegatecall to the stored implementation; tests deploy DvlEngine first, then the proxy, and attach the DvlEngine ABI to the proxy address
upgrader and horsePower are public getters; through the proxy they read the proxy's storage
upgradeToAndCall is payable and keeps any ether sent
