User Story: Upgraded Token with Legacy Forwarding and Monitoring

Title: Serve Legacy Token Transfers Through a New Token Guarded by Detection Bots

As the operator of a token vault
I want the new DET token to execute transfers forwarded by the legacy token while a registered detection bot can veto them
So that legacy holders keep working and the vault's underlying DET stays protected

Acceptance Criteria
1. Deploy the Token
Given the addresses of the legacy token, the vault, the monitoring contract and the player
When DoubleEntryPoint is deployed
Then delegatedFrom, cryptoVault, forta and player should hold those addresses
And 100 ether (100 * 10^18) DET should be minted to the vault
And the deployer should be the owner
2. Standard Token Operations
Given I hold DET
When I call transfer, approve or transferFrom
Then they should behave as a standard OpenZeppelin ERC20
And insufficient balance or allowance should revert with ERC20InsufficientBalance or ERC20InsufficientAllowance
3. Execute a Forwarded Transfer
Given the legacy token has delegated to this contract
When the legacy token calls delegateTransfer(to, value, origSender)
Then value DET should move from origSender to to and the call should return true
And any other caller should be rejected with "Not legacy contract"
4. Notify the Detection Bot
Given the player registered a detection bot in the monitoring contract
When delegateTransfer runs
Then the monitoring contract should be notified with the player and the call data before the transfer
And if the bot raised an alert during the call, the transaction should revert with "Alert has been triggered, reverting"
5. Protect the Vault Underlying
Given the vault's underlying token is set to DET
When anyone calls sweepToken on the vault with DET
Then it should revert with "Can't transfer underlying token"
And sweeping any other token, including the legacy token, must never reduce the vault's DET balance
And sweeping another token should send the vault's whole balance of that token to sweptTokensRecipient

Notes
DoubleEntryPointForta is the monitoring helper: setDetectionBot registers a bot for the caller, notify calls the bot and ignores its failures, raiseAlert counts alerts only when called by the user's registered bot
DoubleEntryPointCryptoVault is the vault helper: constructor(recipient), setUnderlying can be called once (then "Already set"), sweepToken as above
DoubleEntryPointLegacyToken is the legacy ERC20 (LGT) helper: owner-only mint and delegateToNewContract (OwnableUnauthorizedAccount otherwise); its transfer forwards to delegateTransfer once a delegate is set
Tests deploy the monitoring contract, the vault and the legacy token, then DoubleEntryPoint, call setUnderlying(DET), mint LGT to the vault and call delegateToNewContract(DET)
