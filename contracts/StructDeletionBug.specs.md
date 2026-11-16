User Story: Flagged Record Registry

Title: Store, Query and Delete Records with Boolean Flags

As a user of the StructDeletionBug registry
I want to create records identified by an id, mark flag keys on them, read them back and delete them
So that I can manage records whose data, including their flags, is fully under my control

Acceptance Criteria
1. Add a Record with a Flag
Given no record exists for structId
When I call addStruct(structId, flagKeys)
Then the record should store id equal to structId
And the flag for flagKeys should be set to true
2. Add More Flags to a Record
Given a record exists for structId
When I call addStruct again with the same structId and a different flagKeys
Then the new flag should be set to true
And previously set flags should remain true
3. Read a Record
Given a record exists for structId
When I call getStruct(structId, flagKeys)
Then I should receive the stored id and whether that flag is set
And for a flag key that was never set, the flag should be false
And for a structId that was never added, I should receive (0, false)
4. Read the Record Id Through the Public Getter
Given any structId
When I query myStructs(structId)
Then I should receive its stored id, or 0 if it does not exist
5. Delete a Record
Given a record exists for structId with one or more flags set
When I call deleteStruct(structId)
Then the record should be removed completely
And getStruct(structId, flagKeys) should return (0, false) for every flag key previously set
And myStructs(structId) should return 0
6. Re-create a Deleted Record
Given a record was deleted
When I call addStruct with the same structId and a new flag key
Then only the new flag should be set
And none of the flags from before the deletion should be reported as set
Notes
Any account can add, read and delete any record; there is no access control
No events are emitted
