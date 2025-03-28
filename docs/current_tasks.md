# Current Tasks: Implement PATCH /api/v1/concepts/{element_id}

*Last Updated: (Current Date)*

## Focus: Concept PATCH Endpoint

**Goal:** Add functionality to partially update an existing concept by its element ID.

### Tasks:

-   [x] **Pydantic Model (`models/concept.py`):**
    -   [x] Define a new model `ConceptUpdate`.
    -   [x] Ensure all fields in `ConceptUpdate` are optional.
    -   [x] Fix type hints after realizing enums didn't exist.
-   [x] **API Endpoint (`concepts.py`):**
    -   [x] Define `update_concept_partial` function.
    -   [x] Add `@router.patch` decorator.
    -   [x] Implement `model_dump(exclude_unset=True)`.
    -   [x] Handle empty update data case.
    -   [x] Implement Cypher query (`SET c += $update_data`, `RETURN c, elementId(c) AS elementId`).
    -   [x] Execute query.
    -   [x] Handle 404 Not Found.
    -   [x] Process result into `ConceptResponse`, ensuring key consistency (`elementId`).
    -   [x] Add specific `except HTTPException` and generic `except Exception` handlers.
-   [x] **Integration Test (`test_concept_endpoints.py`):**
    -   [x] Create `test_update_concept_partial_success()`:
        -   [x] Arrange: Create concept.
        -   [x] Arrange: Define partial update data.
        -   [x] Act: Call PATCH.
        -   [x] Assert: Check 200 OK status.
        -   [x] Assert: Verify response body reflects updates.
        -   [x] Act/Assert (Verify): Call GET and verify persistence.
    -   [x] Create `test_update_concept_not_found()`:
        -   [x] Arrange: Define non-existent ID and data.
        -   [x] Act: Call PATCH on non-existent ID.
        -   [x] Assert: Check 404 status.
    -   [x] Fix `NameError: PROJECT_ROOT` in `conftest.py`.
    -   [x] Fix import errors related to non-existent `enums.py`.
-   [ ] **Documentation:**
    -   [x] Update this file (`current_tasks.md`) as tasks are completed.
    -   [ ] Update `activeContext.md` and `progress.md` after the feature is fully implemented and tested.

### Notes/Considerations:
- Using `SET c += $update_data` in Cypher is efficient for partial updates.
- Ensure `ConceptUpdate` model correctly defines optional fields.
- Pydantic's `model_dump(exclude_unset=True)` is key.
- Consistency between Cypher alias, record access key, dict key, and Pydantic field name (`elementId`) is crucial. Issue tracked in `icebox.md` for potential future change to snake_case. 