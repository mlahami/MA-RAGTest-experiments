User Story: Wallet With a Bonus Code Registry

Title: Hold Ether and Maintain a List of Bonus Codes

As the owner of a simple Ether wallet
I want the wallet to accept Ether, keep a public-facing list of numeric bonus codes that users can manage, and let only me close the wallet
So that users can participate in a bonus program while the funds and the wallet lifecycle stay under my control

Acceptance Criteria
1. Deploy the Wallet
Given I deploy the SbArbitraryLocationWriteWallet contract
When the deployment succeeds
Then I should be recorded as the owner
And the bonus code list should be empty
2. Receive Ether
Given the wallet is deployed
When anyone sends Ether to the wallet without calling a function
Then the transfer should be accepted
And the wallet balance should increase by the amount sent
3. Add a Bonus Code
Given the wallet is deployed
When any user calls PushBonusCode with a number
Then the number should be appended to the end of the bonus code list
And the list length should increase by 1
4. Remove the Last Bonus Code
Given the bonus code list contains at least one code
When any user calls PopBonusCode
Then the last code should be removed
And the list length should decrease by 1
And if the list is empty, the transaction should revert and the list should remain empty
5. Update a Bonus Code
Given the bonus code list contains codes
When a user calls UpdateBonusCodeAt with an index and a new value
Then the code at that index should be replaced by the new value
And the transaction should revert if the index is not lower than the current number of codes
And updating a code must never modify any other wallet data, in particular the owner
6. Destroy the Wallet
Given I am the owner
When I call Destroy
Then the wallet should be closed and its entire Ether balance sent to me
And if any other address calls Destroy, the transaction should revert

Notes
The bonus code list and the owner address are private and have no getter functions
Bonus code management is open to every user; only the destruction of the wallet is restricted to the owner
The owner is fixed at deployment and there is no function to change it
The list length can never be negative and must always equal the number of codes actually stored
