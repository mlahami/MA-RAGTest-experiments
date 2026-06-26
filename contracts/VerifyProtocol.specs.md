User Story: Verify Protocol (VRFY)
Primary Actor

An autonomous AI agent wallet, or a wallet controlled by a system acting on behalf of an AI agent, which performs transactions and interacts with smart contracts.

Context and Problem

AI agents are increasingly responsible for executing on-chain financial operations such as trading, DeFi interactions, and automated fund management. However, blockchains only verify signature validity, not whether the signer is trustworthy or authorized in a broader sense.

This creates a critical gap: any compromised or malicious agent with a valid private key can still operate freely.

In one documented scenario, a compromised AI routing system led to the loss of significant funds because there was no mechanism to verify the identity or trustworthiness of the executing agent before allowing transactions.

The problem is the absence of an on-chain identity and trust layer for autonomous agents.

Core User Story

As an agent operator, I want to register my wallet as a verified agent by staking VRFY tokens so that other smart contracts can verify my trustworthiness before allowing me to interact with them.

Registration Flow

As a new agent, I call the register function and stake at least the minimum required amount of VRFY tokens.

In return:

My tokens are locked in the protocol as stake
My wallet is recorded as an active agent
A trust profile is created on-chain
I become eligible for verification checks by other contracts

Outcome: The agent is recognized as an economically committed participant with an identity anchored in staked value.

Trust Building Flow

As a registered agent, I want to improve my credibility over time so that I can access more protocols and gain higher trust levels.

I can:

Maintain my stake over time
Increase my stake using the boost function

The trust score is influenced by:

Amount of tokens staked
Duration since registration

Outcome: Trust increases gradually based on economic commitment and time, reflecting reliability.

Revocation Flow

As an agent operator, I may choose to exit the system.

When I call revoke:

My staked tokens are returned
My registration status is deactivated
My trust score is reset to zero

Outcome: Trust is not permanent and must be continuously maintained through participation.

Integration by External Protocols

As a DeFi protocol or smart contract, I want to verify whether an incoming agent is trusted before allowing it to execute sensitive operations.

I do this by calling:

isVerified(agent)

If the result is true:

The agent is allowed to proceed

If false:

The action is rejected

Outcome: Protocols can enforce a simple trust gate using a single boolean check.

Trust Model

The system is based on the principle that trust must be economically backed.

An agent becomes trustworthy through:

Staked capital that is at risk
Time spent maintaining registration
Continued participation in the system

Trust can be lost instantly by revocation, while building it requires sustained commitment.

Identity Layer Outcome

After registration, an agent has:

A blockchain-native identity tied to its wallet
A staked economic commitment
A measurable trust score
A verifiable active status usable by external systems