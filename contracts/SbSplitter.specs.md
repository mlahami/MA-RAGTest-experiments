User Story: Ether Splitter with Puppet Forwarders

Title: Split Owner Funding Equally Between Four Forwarding Wallets

As the owner of a funding splitter
I want my deposit divided equally among four forwarding wallets that pass the funds on to a configured target
So that funds are distributed in equal shares and can be recovered by a master account

Acceptance Criteria
1. Deploy the Splitter
Given a deployer
When the contract is deployed with a puppet target address and a puppet master address
Then the deployer should become owner
And four puppet wallets should be created, each configured with that target and master
And extra slots 0 to 3 should point to the four puppets
And getPuppetCount should return 4
2. Create Additional Puppets
Given I am the owner
When I call newPuppet
Then a new puppet should be deployed and appended to the puppet list
And its address should be returned
And a non-owner should be rejected
3. Update a Recipient Slot
Given any caller
When setExtra is called with a slot id and a non-zero address
Then that slot should point to the new address
And a zero address should be rejected
4. Fund the Puppets
Given I am the owner
When I call fundPuppets with Ether
Then the share should be one quarter of the amount sent
And each of the four recipients in slots 0 to 3 should receive exactly one share
And a non-owner should be rejected
5. All-or-Nothing Funding
Given one of the four recipients rejects its share
When fundPuppets is executed
Then the whole funding transaction should be reverted
And no recipient should be left paid while another is unpaid
And no share should remain stuck in the splitter
6. Puppet Forwarding
Given a puppet receives Ether from any sender other than its target
When the Ether arrives
Then the puppet should forward the full amount to its target
And if forwarding fails the incoming payment should be rejected
And Ether received from the target itself should be kept by the puppet
7. Withdrawals
Given Ether is held by the splitter or a puppet
When the splitter owner calls withdraw on the splitter, or the master calls withdraw on a puppet
Then the full balance should be transferred to that caller
And any other caller should be rejected

Notes
The splitter accepts plain Ether transfers
Any remainder from dividing by four stays in the splitter
Puppet target and master are fixed per puppet at creation
