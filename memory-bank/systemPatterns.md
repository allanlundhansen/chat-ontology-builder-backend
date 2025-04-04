# System Patterns

## Architecture Overview

The KantAI Backend follows a modular architecture based on Kant's epistemological framework, with distinct components corresponding to cognitive faculties:

```
┌─────────────────────────────────────────────────┐
│                  Reason Module                  │
│         (Active Inference & Coherence)          │
└─────────────────────────────────────────────────┘
                        ▲
                        │
┌─────────────┬─────────────────┬─────────────────┐
│ Understanding│    Judgment     │   Imagination   │
│    Module    │     Module      │     Module      │
│  (Neo4j DB)  │ (Classification)│ (Generation)    │
└─────────────┴─────────────────┴─────────────────┘
                        ▲
                        │
┌─────────────────────────────────────────────────┐
│               Action/Sense Layer                │
│             (LLM-based Ingestion)               │
└─────────────────────────────────────────────────┘
                        ▲
                        │
┌─────────────────────────────────────────────────┐
│                External Data                    │
└─────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Neural-Symbolic Integration

- **Logic Tensor Networks (LTNs)**: Used for bidirectional translation between neural embeddings and symbolic representations
- **Graph Neural Networks (GNNs)**: Employed for structural learning on the knowledge graph
- **Symbolic Constraints**: Implemented using SHACL constraints in Neo4j

### 2. Concept Formation

- **Determinant Judgment**: Classification of known inputs using supervised learning
- **Reflective Judgment**: Formation of new concepts through:
  - Inductive reasoning via mini-LLMs
  - Abductive reasoning via GNNs optimizing toward categorical complementarity

### 3. Data Flow Patterns

#### 3.1 Philosophical Model (Kantian Epistemology)

In Kant's epistemology, the cognitive faculties don't operate in a simple sequential pipeline but in a complex, interdependent relationship:

```
                   ┌──────────────────┐
                   │      Reason      │
                   │  (Systematicity  │
                   │   & Coherence)   │
                   └──────────────────┘
                     ▲              ▲
                    /                \
                   /                  \
                  /                    \
   Regulative    /                      \  Strives for
    Principles  /                        \  Unity
               /                          \
              /                            \
             ▼                              ▼
┌──────────────────┐   Mediates   ┌──────────────────┐
│   Understanding  │◄────────────►│     Judgment     │
│   (Categories &  │              │  (Application of │
│    Concepts)     │              │     Concepts)    │
└──────────────────┘              └──────────────────┘
          ▲                                 ▲
          │                                 │
          │           Schematism            │
          │          (Neural-Symbolic       │
          │            Bridge)              │
          │                                 │
          ▼                                 ▼
     ┌──────────────────────────────────────────┐
     │             Imagination                   │
     │   (Productive & Reproductive)             │
     └──────────────────────────────────────────┘
                         ▲
                         │
                         │
                         │
     ┌──────────────────────────────────────────┐
     │             Action/Sense Layer           │
     │           (Sensory Intuition)            │
     └──────────────────────────────────────────┘
                         ▲
                         │
                         │
     ┌──────────────────────────────────────────┐
     │              External Data                │
     └──────────────────────────────────────────┘
```

Key aspects of this philosophical model:

- **Understanding** provides the categories and concepts that structure experience
- **Judgment** mediates between understanding and sensibility, determining how intuitions are subsumed under concepts
- **Reason** regulates the other faculties and strives for systematic unity
- **Imagination** (both productive and reproductive) bridges between sensory intuitions and concepts
- The faculties operate simultaneously with bidirectional interactions, not sequentially
- **Schematism** serves as the procedure by which imagination applies understanding's categories to sensory intuition

#### 3.2 Computational Implementation

While our computational implementation necessarily simplifies this model, we maintain the essential interactions between modules:

- **Bidirectional Processing**:
  - Bottom-up: External Data → Action/Sense → Imagination → Understanding & Judgment → Reason
  - Top-down: Reason → Judgment & Understanding → Imagination → Action/Sense

- **Cross-module Feedback Loops**:
  - Understanding ↔ Judgment: Application of categories to particulars
  - Imagination ↔ Understanding: Structuring of intuitions according to categories
  - Reason ↔ Understanding & Judgment: Global coherence constraints
  - Action/Sense ↔ Imagination: Structuring of raw data

- **Active Inference Framework**: Implements Kant's unity of apperception as a cross-module mechanism that minimizes free energy and maintains global coherence

### 4. Knowledge Representation

- **Neo4j Graph Database**: Stores concepts and relationships according to Kant's categorical structure
- **Hierarchical Categories**: Quantity, Quality, Relation, and Modality categories organize all concepts. (Note: Phase 1 uses properties for Quality/Modality, planned for replacement in Phase 2. Value validation for Phase 1 properties enforced at application level due to DB limitations).
- **Relationship Types**: Specialized predicates for different categorical dimensions
- **Cypher Query Endpoints**: Dedicated API endpoints for executing optimized Cypher queries against the knowledge graph.
- **Query Management**: All Cypher queries are defined as Python string constants within modules in the `src/cypher_queries/` directory (e.g., `concept_queries.py`, `relationship_queries.py`, `specialized_queries.py`). The previous file-based loader (`cypher_loader.py`) has been removed.
- **Direct Cypher Interface**: Advanced endpoint allowing direct Cypher execution for complex queries and power users
- **API Evolution**: API design must account for the planned Phase 2 transition from property-based to judgment-based modality, including deprecation warnings and new endpoints.
- **Validation Layer**: New validation service enforces Quality/Modality constraints and relationship rules before database writes
- **Deprecation Warnings**: API responses for Concept endpoints now include warnings about Phase 2 modality migration
- **Logging**: Standardized logging using Python's `logging` module is implemented, particularly in core API endpoints like `concepts.py`.

## Technical Decisions

### Database Selection

- **Neo4j**: Chosen for its native graph representation, SHACL constraint support, and Cypher query language
- **Vector Database Integration**: For storing and retrieving neural embeddings alongside symbolic representations

### LLM Integration

- **External API Connections**: For production deployments with state-of-the-art models
- **Local Open-Source Models**: For development and scenarios requiring data privacy
- **Specialized Fine-tuning**: LLMs fine-tuned on the ontology structure for the productive imagination component

### API Design

- **RESTful Architecture**: For standard HTTP interactions
- **WebSocket Support**: For real-time updates in chat and visualization
- **Resource-Oriented Paths**: Structure API paths based on the primary resource being accessed.
  - **Decision (Phase 1):** Use `/api/v1/concepts` as the base path for endpoints related to concepts within the Understanding Module (both those returning concept lists and those detailing relationships *of* a specific concept, e.g., `/api/v1/concepts/{id}/properties`). This reflects the current focus on concepts-as-objects-of-understanding.
  - **Rationale:** While "concepts" exist in both Understanding and General Logic (via Judgments), using `/concepts` for the Understanding module's entities is pragmatic for Phase 1. Clear boundaries will be maintained by introducing distinct paths (e.g., `/api/v1/logic` or `/api/v1/judgments`) for General Logic components in future phases. This balances current scope clarity with long-term modularity.
- **Cypher Query Endpoints**: Dedicated API endpoints for executing optimized Cypher queries against the knowledge graph, often using predefined templates.
- **Query Management**: All Cypher queries are defined as Python string constants within modules in the `src/cypher_queries/` directory (e.g., `concept_queries.py`, `relationship_queries.py`, `specialized_queries.py`). The previous file-based loader (`cypher_loader.py`) has been removed.
- **Direct Cypher Interface**: Advanced endpoint allowing direct Cypher execution for complex queries and power users
- **API Evolution**: API design must account for the planned Phase 2 transition from property-based to judgment-based modality, including deprecation warnings and new endpoints.
- **Validation Layer**: New validation service enforces Quality/Modality constraints and relationship rules before database writes
- **Deprecation Warnings**: API responses for Concept endpoints now include warnings about Phase 2 modality migration
- **Logging**: Standardized logging using Python's `logging` module is implemented, particularly in core API endpoints like `concepts.py`.

### Containerization and Deployment

- **Docker**: For consistent development and deployment environments
- **Kubernetes**: For orchestration in production environments
- **Microservices Architecture**: Each cognitive module implemented as a separate service
- **Code Documentation**: Inline documentation and code quality standards
- **Memory Bank**: Project state and context maintained in `/memory-bank` directory.

## Development Patterns

### Testing Strategy

- **Unit Tests**: For individual components
- **Integration Tests**: For module interactions
    - **Data Creation Pattern**: Tests requiring specific data setups (e.g., for checking relationships or specific concepts) should create that data within the test function itself using the `async_client`. This avoids reliance on globally loaded sample data or brittle, hardcoded element IDs.
    - **Isolation**: Use fixtures like `@pytest.mark.usefixtures("clear_db_before_test")` to ensure each test runs against a clean database state, preventing interference between tests.
- **Cognitive Tests**: Specialized tests for evaluating reasoning capabilities
- **Validation Test Suite**: New pattern of "constraint violation" tests ensuring invalid data gets rejected at API boundaries

### CI/CD Pipeline

- **GitHub Actions**: For automated testing and deployment
- **Continuous Integration**: Ensuring code quality and compatibility
- **Staged Deployments**: Development → Testing → Production

### Documentation

- **API Documentation**: OpenAPI/Swagger for API endpoints
- **Architecture Documentation**: Comprehensive documentation of system architecture and principles
- **Code Documentation**: Inline documentation and code quality standards

## Data Flow and Validation

- **Cypher Query Design**: Cypher queries, especially those returning complex nested structures (like paths with nodes and relationships), must be carefully designed.
    - **Pydantic Alignment**: The structure returned by the query (key names, data types) MUST precisely match the Pydantic models used for response validation in the API endpoint (e.g., use `start_node_id` in Cypher if the Pydantic model expects `start_node_id`).
    - **Explicit Projections**: Use explicit map projections (`node {{.*, elementId: elementId(node)}}`, `rel {{..., properties: properties(rel)}}`) to control exactly which fields are returned, including nested properties.
    - **Parameterization**: Always use parameterized queries (`$paramName`) to prevent injection vulnerabilities.
    - **String Formatting**: If string formatting is necessary (e.g., for dynamic relationship types or query limits), use Python's f-strings or `.format()` carefully, ensuring literal curly braces within the Cypher itself are escaped (`{{`, `}}`).
- **Datetime Handling**: Neo4j returns datetime objects (`neo4j.time.DateTime`). These need conversion (e.g., using `convert_neo4j_datetimes` utility) before validation with Pydantic models that expect standard Python `datetime` or string representations.
- **Endpoint `/concepts/{id}/relationships`**: This endpoint (`get_all_relationships_for_concept`) is implemented to return a list of all relationships connected to a concept, consistently formatted according to the `RelationshipResponse` model. It no longer attempts to map specific relationship types (like `PRECEDES` or `SPATIALLY_RELATES_TO`) to more specialized Pydantic models within its own logic, aligning its internal behavior with its declared API contract (`response_model=List[RelationshipResponse]`). Specialized relationship details are handled by dedicated endpoints (e.g., `/concepts/{id}/temporal`). 