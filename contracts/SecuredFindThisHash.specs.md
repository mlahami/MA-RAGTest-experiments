User Story: Commit-Reveal Hash Puzzle

Title: Win a Funded Reward by Committing to and Then Revealing the Preimage of a Published Hash

As a puzzle participant
I want to first commit a hidden fingerprint of my answer and reveal it in a later block
So that the first participant who correctly reveals the answer receives the reward

Acceptance Criteria
1. Fund the Puzzle
Given a deployer
When SecuredFindThisHash is deployed with Ether
Then reward should equal the Ether sent
And hash should hold the published target hash, winner should be the zero address and ended should be false
2. Commit a Solution
Given the game is not ended and I have not committed before
When I call commitSolution with keccak256(abi.encodePacked(myAddress, solution, secret))
Then my commitment should be stored with the current block timestamp and revealed set to false
And the call should revert with "Already committed" if I already committed
And it should revert with "Already ended" once the game is over
3. Read My Commitment
Given the game is not ended
When I call getMySolution
Then I should receive my committed hash, commit time and revealed flag
And it should revert with "Not committed yet" if I have no commitment
4. Reveal the Solution
Given I committed in an earlier block and the game is not ended
When I call revealSolution with my solution and secret
Then the contract should check that keccak256(abi.encodePacked(msg.sender, solution, secret)) equals my commitment
And that keccak256(abi.encodePacked(solution)) equals hash
And I should be recorded as winner, ended should become true and the reward should be sent to me
5. Reveal Failures
Given an invalid reveal
When I call revealSolution
Then it should revert with "Not committed yet", "Cannot reveal in the same block", "Already committed and revealed", "Hash doesn't match" or "Incorrect answer" as applicable
And if the reward payment fails it should revert with "Failed to send ether." leaving winner and ended unchanged

Notes
Each address may commit only once
The game ends after the first successful reveal; afterwards commit, read and reveal calls revert with "Already ended"
No events are emitted
The target hash is fixed in the contract; tests need a known matching solution to reach the winning path, otherwise they focus on commitment and failure paths
