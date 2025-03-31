# Current Tasks: Complete Phase 1 API Endpoints

*Last Updated: 2024-08-05*

## Focus: Testing & Cleanup

**Goal:** Address outstanding testing and consistency issues, and perform final cleanup for Phase 1 API work.

### Tasks:

-   [X] **Relationships (`/api/v1/relationships`)**:
    -   [X] **GET /{element_id}:**
        -   [X] Define Pydantic response model (reuse `RelationshipResponse`?).
        -   [X] Implement API endpoint function.
        -   [X] Write Cypher query to fetch a single relationship by `elementId`.
        -   [X] Handle 404 Not Found.
        -   [X] Add integration test.
    -   [X] **PATCH /{element_id}:**
        -   [X] Define `RelationshipUpdate` Pydantic model (optional fields).
        -   [X] Implement API endpoint function.
        -   [X] Write Cypher query for partial update (`SET r += $update_data`).
        -   [X] Handle 404 Not Found.
        -   [X] Add integration test.
    -   [X] **DELETE /{element_id}:**
        -   [X] Implement API endpoint function.
        -   [X] Write Cypher query to delete a relationship (`MATCH ()-[r]-() WHERE elementId(r) = $id DETACH DELETE r`).
        -   [X] Handle 404 Not Found.
        -   [X] Return 204 No Content on success.
        -   [X] Add integration test.
-   [X] **Query Management Refactoring:**
    -   [X] Migrate all concept queries to Python constants in a dedicated module.
    -   [X] Migrate all relationship queries to Python constants in a dedicated module.
    -   [X] Migrate all category queries to Python constants in a dedicated module.
    -   [X] Migrate all specialized queries to Python constants in a dedicated module.
    -   [X] Add deprecation notice to `query_templates.cypher`.
    -   [X] Delete deprecated `cypher_loader.py`.
    -   [X] Update code to use the new constants directly.
    -   [X] Ensure tests pass with the refactored code.
    -   [X] Document migration status in `memory-bank/query_migration_status.md`.
-   [ ] **Categories (`/api/v1/categories`)**:
    -   [X] Define Pydantic models (e.g., `CategoryResponse`, `SubCategoryResponse`, `CategoryListResponse`).
    -   [X] Implement `GET /` endpoint (list all categories and subcategories).
    -   [X] Implement `GET /{name}` endpoint (get specific category/subcategory details).
    -   [-] Implement `POST /` endpoint (create a top-level category) - **Skipped**: See Note below.
    -   [-] Implement `POST /{parent_name}/subcategories` endpoint (create a subcategory) - **Skipped**: See Note below.
    -   [-] Implement `PATCH /{name}` endpoint (update category/subcategory) - **Skipped**: See Note below.
    -   [-] Implement `DELETE /{name}` endpoint (delete category/subcategory, handle children) - **Skipped**: See Note below.
    -   [X] Add integration tests for GET endpoints.
    -   [-] Add integration tests for POST, PATCH, DELETE endpoints - **Skipped**: See Note below.
-   [ ] **Testing Refinement:**
    -   [ ] Investigate and fix skipped tests in `test_concepts.py` and `test_concept_endpoints.py`.
    -   [ ] Investigate and fix 7 test warnings (Pytest mark, Neo4j UserWarning).
-   [ ] **Consistency & Cleanup:**
    -   [X] Address API Naming Convention (`elementId` vs `element_id`) - see `icebox.md`.
    -   [ ] Review and remove any remaining unnecessary debug code or comments.
-   [ ] **Documentation:**
    -   [ ] Update this file (`current_tasks.md`) as tasks are completed.

### Notes/Considerations:
- **Category Modification Endpoints (POST/PATCH/DELETE) Skipped**: Decided to omit these endpoints for Phase 1 as the Kantian category structure is pre-defined and fixed. Modifications via the API are philosophically inconsistent with the model. The API will only support retrieving category information.
- Fixing skipped tests might involve adjusting fixtures or test logic.
- Remember to update all relevant memory-bank files after completing major tasks.