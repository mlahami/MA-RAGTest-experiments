User Story: Multi-Owner Ether Vault

Title: Share Control of an Ether Vault Among a Tree of Owners

As the root owner of a shared Ether vault
I want existing owners to be able to appoint and remove other owners, and owners to withdraw the vault funds
So that a trusted group can manage the funds while every owner remains traceable to the owner who appointed them

Acceptance Criteria
1. Deploy the Vault
Given I deploy the SbMultiOwned contract
When the deployment succeeds
Then I should be stored as root
And owners(root) should return my own address, marking me as an owner
2. Receive Ether
Given the vault is deployed
When anyone sends Ether to the vault without calling a function
Then the transfer should be accepted and the vault balance should increase
3. Appoint a New Owner
Given I am an existing owner
When I call newOwner with a non-zero address
Then that address should become an owner with me recorded as its parent in owners
And the call should return true
And the transaction should revert if the address is the zero address
And the transaction should revert if the caller is not an existing owner
4. Remove an Owner
Given I am an existing owner
When I call deleteOwner for an owner that I appointed, or I am the root and the target is any existing owner
Then the target should no longer be an owner and owners(target) should return the zero address
And the call should return true
And the transaction should revert if the caller is not an owner
And the transaction should revert if the caller is neither the parent of the target nor the root
5. Withdraw All Funds
Given I am an existing owner
When I call withdrawAll
Then the entire vault balance should be transferred to me
And the transaction should revert if the caller is not an owner

Notes
The owners mapping is public: an address is an owner when its recorded parent is non-zero
Ownership forms a tree rooted at the deployer; the root cannot be replaced
Non-owners can only deposit Ether; they must never be able to appoint themselves or others as owners
Removing an owner does not automatically remove the owners that it appointed
