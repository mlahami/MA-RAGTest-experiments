User Story: Town Crier Oracle Request Service

Title: Pay a Fee to Request Off-Chain Data Delivered Through a Callback

As a decentralized application developer
I want to submit paid data requests that an authorized SGX oracle account answers through a callback
So that my contract consumes trusted off-chain data and fees are settled fairly

Acceptance Criteria
1. Deploy the Service
Given a deployer
When the contract is deployed with the SGX oracle address
Then the deployer should be the administrator
And requestCnt should be 1
2. Submit a Request
Given the service is running
When I call request with a type, callback address, function id, timestamp and data, paying at least MIN_FEE
Then a new request should be stored, RequestInfo emitted and its id returned
And paying less than MIN_FEE should refund me and return FAIL_FLAG
And with the killswitch on my payment should be refunded and newVersion returned
3. Deliver a Response
Given a pending request
When the SGX account calls deliver with the matching parameter hash
Then the request should be marked delivered and unrespondedCnt decreased
And for error codes below 2 the fee should be paid to the SGX account
And for error codes of 2 or more the fee should be refunded to the requester
And DeliverInfo should be emitted and the callback invoked with the id, error and response
And deliveries from other accounts, for unknown or delivered requests, or with a wrong hash should be ignored
4. Settlement Must Succeed
Given a delivery requires paying the SGX account or refunding the requester
When that payment fails
Then the delivery should be reverted
And the request must not end up delivered with its fee unsettled
5. Deliver a Cancelled Request
Given a cancelled request
When the SGX account delivers it
Then the cancellation fee should be paid to the SGX account, reverting on failure, and the request marked delivered
6. Cancel a Request
Given I am the requester and the remaining fee covers the cancellation fee
When I call cancel
Then I should get the fee minus the cancellation fee back, the request be marked cancelled and Cancel emitted with flag 1
And otherwise Cancel should be emitted with flag -1 and FAIL_FLAG returned
7. Administration
Given I am the administrator
When I call upgrade, reset, suspend, restart or withdraw
Then upgrade should record the new version and enable the killswitch, reset should update fees and emit Reset, suspend and restart should toggle the killswitch, and withdraw should send me the balance
And upgrade, reset and withdraw should only act with no pending requests
And calls from other accounts should have no effect

Notes
The contract does not accept plain Ether transfers
