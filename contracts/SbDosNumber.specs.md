User Story: Growable Number Store With Bulk Insert and Reset

Title: Insert Many Copies of a Number and Reset the Store When It Is Large

As a user of an on-chain number store
I want to append a value several times in one call and reset the store once it holds many elements
So that I can fill and reuse a shared list of numbers efficiently

Acceptance Criteria
1. Initial State
Given the SbDosNumber contract is deployed
When I query it
Then getLengthArray should return 0
And getRealLengthArray should return 0
2. Insert Numbers
Given the store is deployed
When I call insertNnumbers with a value and a count
Then the value should be written count times after the current logical end of the list
And getLengthArray should increase by count
And storage slots that already exist beyond the logical end should be reused before the underlying array grows
And getRealLengthArray should only grow when the logical length would exceed it
3. Insert Zero Numbers
Given the store is deployed
When I call insertNnumbers with a count of 0
Then nothing should change
4. Soft Reset
Given the store holds more than 1500 elements
When I call clear
Then getLengthArray should return 0
And the underlying array should be kept, so getRealLengthArray stays unchanged
And subsequent inserts should overwrite the existing slots from position 0
And if the store holds 1500 elements or fewer, the call should revert
5. Full Reset
Given the store holds more than 1500 elements
When I call clearDOS
Then the underlying array should be emptied
And both getLengthArray and getRealLengthArray should return 0
And if the store holds 1500 elements or fewer, the call should revert
6. Availability
Given any number of elements has been stored
When users call insertNnumbers with reasonable counts, clear or clearDOS
Then the operations should complete within the block gas limit so the store always remains usable

Notes
Any address may insert or reset; there is no owner
The logical length and the physical array length are tracked separately
Values are stored as unsigned 256-bit integers
A reset is only allowed once more than 1500 elements have been stored
