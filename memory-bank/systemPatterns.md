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
- **Cypher Query Endpoints**: Dedicated API endpoints for executing optimized Cypher queries against the knowledge graph, often using predefined templates.
- **Query Templates**: Pre-defined Cypher query templates (`.cypher` files) for common knowledge graph operations, executed by the application layer. (Note: APOC custom procedures are unavailable).
- **Direct Cypher Interface**: Advanced endpoint allowing direct Cypher execution for complex queries and power users
- **API Evolution**: API design must account for the planned Phase 2 transition from property-based to judgment-based modality, including deprecation warnings and new endpoints.

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
- **Query Templates**: Pre-defined Cypher query templates (`.cypher` files) for common knowledge graph operations, executed by the application layer. (Note: APOC custom procedures are unavailable).
- **Direct Cypher Interface**: Advanced endpoint allowing direct Cypher execution for complex queries and power users
- **API Evolution**: API design must account for the planned Phase 2 transition from property-based to judgment-based modality, including deprecation warnings and new endpoints.

### Containerization and Deployment

- **Docker**: For consistent development and deployment environments
- **Kubernetes**: For orchestration in production environments
- **Microservices Architecture**: Each cognitive module implemented as a separate service

## Development Patterns

### Testing Strategy

- **Unit Tests**: For individual components
- **Integration Tests**: For module interactions
- **Cognitive Tests**: Specialized tests for evaluating reasoning capabilities

### CI/CD Pipeline

- **GitHub Actions**: For automated testing and deployment
- **Continuous Integration**: Ensuring code quality and compatibility
- **Staged Deployments**: Development → Testing → Production

### Documentation

- **API Documentation**: OpenAPI/Swagger for API endpoints
- **Architecture Documentation**: Comprehensive documentation of system architecture and principles
- **Code Documentation**: Inline documentation and code quality standards 