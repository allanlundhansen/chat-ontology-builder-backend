# Current Tasks: Complete Phase 1 API Endpoints

*Last Updated: 2024-08-02*

## Focus: Relationships, Categories, & Refinement

**Goal:** Implement the remaining CRUD endpoints for relationships, implement all endpoints for categories, and address outstanding testing and consistency issues.

### Tasks:

-   [ ] **Relationships (`/api/v1/relationships`)**:
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
-   [ ] **Categories (`/api/v1/categories`)**:
    -   [X] Define Pydantic models (e.g., `CategoryResponse`, `SubCategoryResponse`, `CategoryListResponse` - Create/Update needed).
    -   [X] Implement `GET /` endpoint (list all categories and subcategories).
    -   [X] Implement `GET /{name}` endpoint (get specific category/subcategory details).
    -   [ ] Implement `POST /` endpoint (create a top-level category).
    -   [ ] Implement `POST /{parent_name}/subcategories` endpoint (create a subcategory).
    -   [ ] Implement `PATCH /{name}` endpoint (update category/subcategory).
    -   [ ] Implement `DELETE /{name}` endpoint (delete category/subcategory, handle children).
    -   [X] Add integration tests for GET endpoints.
    -   [ ] Add integration tests for POST, PATCH, DELETE endpoints.
-   [ ] **Testing Refinement:**
    -   [ ] Investigate and fix skipped tests in `test_concepts.py` and `test_concept_endpoints.py`.
-   [ ] **Consistency & Cleanup:**
    -   [X] Address API Naming Convention (`elementId` vs `element_id`) - see `icebox.md`.
    -   [ ] Review and remove any remaining unnecessary debug code or comments.
-   [ ] **Documentation:**
    -   [ ] Update this file (`current_tasks.md`) as tasks are completed.
    -   [ ] Update `activeContext.md` and `progress.md` after significant features are implemented.

### Notes/Considerations:
- Relationship queries should return source/target node details or just IDs? Decide on response structure.
- Category structure is pre-defined; API might primarily be for retrieval in Phase 1.
- Fixing skipped tests might involve adjusting fixtures or test logic. 