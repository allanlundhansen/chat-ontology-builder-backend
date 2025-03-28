# Icebox - Deferred Tasks & Improvements

*Last Updated: (Current Date)*

This file tracks tasks, improvements, or issues that have been identified but are not part of the immediate work cycle defined in `current_tasks.md`. They should be revisited and prioritized later.

## Tasks

-   **API Naming Convention:**
    -   **Issue:** API responses currently use `camelCase` (e.g., `elementId`) due to default Pydantic serialization, while Python code uses `snake_case` (`element_id`). This was observed in the `POST /concepts` response.
    -   **Goal:** Enforce consistent `snake_case` in all API JSON request/response bodies to align with Python conventions.
    -   **Action:**
        -   Investigate Pydantic models (e.g., `ConceptResponse`, `RelationshipResponse`) in `src/models/`.
        -   Adjust model configurations (e.g., remove `alias`, use `model_dump(by_alias=False)`) to ensure `snake_case` output.
        -   Update relevant tests to expect `snake_case` keys.
        -   Document the `snake_case` convention for API JSON (e.g., in `systemPatterns.md` or `techContext.md`).

-   **(Add other deferred tasks here as they arise)** 