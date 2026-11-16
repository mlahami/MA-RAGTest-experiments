User Story: Signature-Controlled Lock Factory

Title: Deploy Locks Controlled by the Signer of Their Lock Id

As the operator of a smart-lock service
I want to deploy locks whose controller is the account that signed the lock id
So that only that controller can open a lock or hand it over to someone else

Acceptance Criteria
1. Deploy the Factory
Given an initial lock counter value
When Impersonator is deployed
Then lockCounter should equal that value and the deployer should be the owner
2. Deploy a New Lock
Given I am the owner
When I call deployNewLock(signature)
Then lockCounter should increase by 1 and a new ImpersonatorECLocker with lockId equal to the new counter should be appended to lockers
And a NewLock event with the lock address, lockId, timestamp and signature should be emitted
And a non-owner caller should be rejected with OwnableUnauthorizedAccount
3. Initialize the Lock
Given signature is abi.encode(r, s, v) of an Ethereum signed message over the 32-byte lockId
When the lock is created
Then msgHash should be the Ethereum signed message hash of lockId and controller should be the recovered signer
And the deployment signature should be marked as used and a LockInitializated event emitted
And deployment should revert with InvalidSignature() when the signature cannot be recovered
4. Open the Lock
Given the controller signed msgHash and that signature was never used
When anyone calls open(v, r, s)
Then an Open event with the controller and the timestamp should be emitted and the signature marked as used
And a signature not recovering to the controller, or failing recovery, should be rejected with InvalidController
And a signature already used, including the deployment signature or any equivalent (v, r, s) form of an accepted authorization, should be rejected with SignatureAlreadyUsed
5. Change the Controller
Given a valid unused controller signature
When anyone calls changeController(v, r, s, newController)
Then controller should become newController and a ControllerChanged event should be emitted
And the same InvalidController and SignatureAlreadyUsed rules apply
And after the change only signatures of newController should open the lock

Notes
ImpersonatorECLocker is the lock helper created by deployNewLock; tests read lockers(i) and attach the ImpersonatorECLocker ABI
Tests sign the 32-byte lockId with signMessage and pass abi.encode(r, s, v) to deployNewLock
lockId, msgHash, controller and usedSignatures are public getters
