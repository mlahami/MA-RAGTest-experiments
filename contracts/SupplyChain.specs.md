User Story: Blockchain-Based Supply Chain Tracking System

Title: Track and Update Package Delivery Stages on Blockchain

As a manufacturer, logistics provider, or authorized carrier
I want to create packages and update their delivery status through predefined steps
So that I can transparently track the full lifecycle of a shipment in an immutable system

Acceptance Criteria
1. Create a Package
Given I am an authorized carrier or the system owner
When I create a new package with a description and initial location
Then:
A unique package ID should be generated
The package should be stored with status set to CREATED
The manufacturer field should record the creator
The initial tracking step should be added to the history
And a PackageCreated event should be emitted
2. Authorize Carriers
Given I am the contract owner
When I authorize a new carrier address
Then that address should be allowed to create and update packages
And unauthorized addresses should be rejected from restricted actions
3. Update Shipment Status
Given a package exists
And I am an authorized carrier or owner
When I update the package status
Then:
The status should move forward in the delivery lifecycle
The system should prevent reverting to previous states
The location and timestamp should be recorded in history
And a StepUpdated event should be emitted
4. Maintain Tracking History
Given a package is created and updated over time
When status changes occur
Then each update should be appended to a historical log containing:
Status
Location
Timestamp
Address of updater
5. Retrieve Full Package History
Given a package exists
When I request its history
Then I should receive a chronological list of all tracking steps
6. Enforce Access Control
Given any user interacts with the contract
When they attempt restricted actions
Then only the owner or authorized carriers should be allowed
And all others should be rejected
Notes
The supply chain follows a strict forward-only state progression (no rollback allowed)
Each package maintains a complete immutable tracking history
Authorization is centrally controlled by the contract owner
Suitable for logistics, shipping, and product traceability systems
Can be extended with roles (manufacturer, transporter, receiver) or NFT-based tracking