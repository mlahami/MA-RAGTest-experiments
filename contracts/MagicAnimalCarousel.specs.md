User Story: Animal Carousel

Title: Place Named Animals in a Rotating Ring of Crates

As a visitor of the magic carousel
I want to put my animal in the next crate of the ring and rename animals in my crates
So that the carousel rotates through crates each holding one animal and its owner

Acceptance Criteria
1. Deploy the Carousel
Given the carousel is deployed
Then currentCrateId should be 0
And crate 0 should store a next-crate id of 1 and no animal or owner
And MAX_CAPACITY should equal 65535
2. Encode an Animal Name
Given a name of at most 12 bytes
When anyone calls encodeAnimalName(name)
Then it should return the name bytes left-aligned in a 96-bit number
And a name longer than 12 bytes should revert with AnimalNameTooLong
3. Add an Animal and Spin
Given the current crate points to a next crate id
When I call setAnimalAndSpin(name)
Then the next crate should store exactly the new animal name (its first 10 bytes), replacing any previous animal, with me as owner
And its next-crate id should be (that crate id + 1) modulo MAX_CAPACITY
And currentCrateId should become that crate id
And a name longer than 12 bytes should revert with AnimalNameTooLong
4. Rename an Animal
Given a crate that has been used and I am its recorded owner, or it has no owner
When I call changeAnimal(name, crateId) with a non-empty name
Then the crate's animal should be replaced by the new name and I should become its owner
And the crate's next-crate id must remain unchanged, so the rotation order is not affected
And the call should revert without a message if another account owns the crate
And it should revert with CrateNotInitialized if the crate was never written
5. Release a Crate
Given I own a crate
When I call changeAnimal with an empty name
Then the crate should keep its animal and next-crate id
And its owner should be cleared so that anyone can rename it later
6. Read Crates
Given any crate id
When anyone reads carousel(crateId)
Then it should return the packed value: owner in bits 0-159, next-crate id in bits 160-175 and animal name in bits 176-255

Notes
Crate ids wrap around after MAX_CAPACITY so the crates form a ring
There are no events and no administrator role
