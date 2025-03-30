# Kantian Category Structure Knowledge Graph - Product Requirements Document

## 1. Overview

This project involves implementing the core Neo4j knowledge graph schema based on Kant's categorical framework. This schema will serve as the foundation for the Understanding Module, providing a structured organization of knowledge according to the four primary Kantian categories: Quantity, Quality, Relation, and Modality. In Kant's epistemology, these categories represent the fundamental concepts that structure experience, distinct from both the formal structures of General Logic and empirical concepts derived from experience.

## 2. Problem Statement

The KantAI backend requires a robust, philosophically grounded knowledge representation that can organize concepts according to Kant's epistemological framework. Current knowledge graph approaches lack the specific categorical structure needed to implement a truly Kantian cognitive architecture. We need to create a Neo4j schema that faithfully represents Kant's categories and their subdivisions while enabling efficient storage and retrieval of knowledge, maintaining proper distinction between the categorical framework (Understanding) and formal logical structures (General Logic).

## 3. Goals & Objectives

- Create a Neo4j database schema that implements Kant's categorical framework
- Define node types, edge types, and properties that represent the four main categories and their subdivisions
- Establish clear boundaries between categories of Understanding and formal structures of General Logic
- Enable efficient querying and traversal of the knowledge graph
- Support the future implementation of SHACL constraints
- Establish the foundation for the Understanding Module of the KantAI architecture
- Create appropriate interfaces for organizing empirical concepts through the categorical framework

## 4. User Stories

- As a developer, I want to store concepts according to their categorical type so that the system can reason about them in a Kantian framework
- As a knowledge engineer, I want to create relationships between concepts that reflect Kantian categories like causality and substance-accident
- As a system architect, I want a knowledge graph structure that can scale as the system ingests new information
- As an AI researcher, I want to query the knowledge graph to analyze how concepts are organized within the Kantian framework

## 5. Functional Requirements

### 5.1 Category Node Structure

- Implement four top-level category nodes: Quantity, Quality, Relation, and Modality
- For each category, implement the three subdivisions as defined by Kant:
  - Quantity: Unity, Plurality, Totality
  - Quality: Reality, Negation, Limitation
  - Relation: Substance / Accident, Causality, Community
  - Modality: Possibility / Impossibility, Existence / Non-existence, Necessity / Contingency
- Define properties for each category type, including:
  - Name
  - Description
  - Formal definition
  - Examples

### 5.2 Concept Node Structure

- Implement a generic Concept node type with properties:
  - ID
  - Name
  - Description
  - Creation timestamp
  - Confidence score
  - Stability status (ephemeral or stable)
  - Source information
  - Quality (optional): Represents the concept's classification under Kant's Quality category; constrained to valid values: "Reality", "Negation", "Limitation"
  - Modality (optional): Represents the concept's classification under Kant's Modality category; constrained to valid values: "Possibility / Impossibility", "Existence / Non-existence", "Necessity / Contingency"
- Enable concepts to be classified under multiple categorical aspects
- Support both primitive and complex concepts

### 5.3 Relationship Types

- Implement INSTANCE_OF as the primary classification mechanism:
  - Connects Concept nodes to appropriate Subcategory nodes for Quantity and Relation categories
  - Example: (Concept)-[:INSTANCE_OF]->(Subcategory:Unity)
- Implement semantic relationships between concepts:
  - HAS_PROPERTY: Connects concepts to their properties/attributes
  - CAUSES: Represents causal relationships between concepts
  - INTERACTS_WITH: Represents reciprocal interactions between concepts
  - CONTAINS: Represents containment or inclusion relationships
  - IS_PART_OF: Represents part-whole relationships
- Implement temporal and spatial relationships (reflecting Kant's Forms of Intuition):
  - PRECEDES: Represents temporal ordering with properties:
    - temporal_distance
    - temporal_unit (constrained to standard time units)
    - confidence
  - SPATIALLY_RELATES_TO: Represents spatial relationships with properties:
    - relation_type (e.g., "above", "contains", "adjacent")
    - distance (optional)
    - unit (optional)
    - confidence
- Each relationship should have common properties:
  - Confidence score
  - `created_at`: Timestamp of creation.
  - `updated_at`: Timestamp of last update (set on PATCH).
  - Source information
  - Temporal qualifiers (if applicable)

### 5.4 Query Capabilities

- Create Cypher queries to retrieve concepts by category:
  - By Quality and Modality properties
  - By INSTANCE_OF relationships to Quantity and Relation subcategories
- Implement queries to navigate causal chains
- Support queries for temporal sequences using PRECEDES relationships
- Support queries for spatial relationships using SPATIALLY_RELATES_TO relationships
- Support queries that filter by confidence thresholds
- Enable retrieval of all categorical relationships for a given concept

## 6. Technical Considerations

### 6.1 Performance

- Implement appropriate indices for efficient retrieval of concepts by category
- Create indices for Quality and Modality properties to optimize queries
- Optimize graph structure for traversal of categorical relationships
- Consider partitioning strategies for scaling as the knowledge base grows
- Implement caching mechanisms for frequently accessed categorical structures

### 6.2 Integration Requirements

- Design the schema to support future SHACL constraints
- Ensure compatibility with Logic Tensor Networks for the neural-symbolic bridge
- Create clear interfaces with the General Logic Module while maintaining proper boundaries
- Prepare for integration with the Action/Sense Layer
- Consider serialization formats for API responses
- Establish patterns for how empirical concepts are organized through the categories

### 6.3 Data Storage

- Design efficient property structures that minimize redundancy
- Implement appropriate data types for confidence scores and timestamps
- Consider compression strategies for description fields
- Plan for backup and recovery procedures

## 7. Acceptance Criteria

- The Neo4j database successfully implements all four Kantian categories and their subdivisions
- The system maintains proper philosophical distinction between categories (Understanding) and formal logical structures (General Logic)
- Concept nodes can be created with optional Quality and Modality properties constrained to valid subcategory values
- Concepts can be classified under Quantity and Relation subcategories using the INSTANCE_OF relationship
- All semantic relationship types (CAUSES, HAS_PROPERTY, etc.) are implemented and can be created between concepts
- Temporal (PRECEDES) and spatial (SPATIALLY_RELATES_TO) relationships are properly implemented with appropriate properties
- Basic queries can retrieve concepts by all four categories using the hybrid approach (properties and relationships)
- The schema accommodates both simple and complex concepts
- Documentation of the schema is complete and clear, including proper explanation of Kantian distinctions and the hybrid implementation approach
- Sample data demonstrating the categorical structure is provided

## 8. Future Considerations (v2)

- Integration with external ontologies and knowledge bases
- Versioning system for evolving concepts
- Support for multi-language concept representations
- Reasoning capabilities directly within the graph database
- Performance optimizations for large-scale knowledge representation

## 9. Implementation Plan

We'll split the implementation into smaller, manageable tasks:

### Task 1: Database Setup and Category Structure
- [x] Set up Neo4j database instance
- [x] Create schema for the four primary categories
- [x] Implement the subcategories for each primary category
- [x] Add properties to category nodes
- [x] **Steps to Test**: Verify that all categories and subcategories exist in the database with appropriate properties (Done via schema inspection/manual checks)

### Task 2: Concept Node Implementation
- [x] Define the Concept node type with all required properties
- [x] Add Quality and Modality properties with appropriate constraints (**Note:** Application-level validation implemented and tested via API)
- [ ] Implement INSTANCE_OF relationships for classification under Quantity and Relation subcategories
- [x] Create indices for efficient concept retrieval, including indices for Quality and Modality properties
- [x] **Steps to Test**: Create sample concepts and verify they can be properly classified using both properties and relationships (Partially done via `POST /concepts` API tests for property validation and `GET /concepts/{id}` for retrieval). Concept CRUD fully tested.

### Task 3: Relationship Type Implementation
- [ ] Create semantic relationship types (CAUSES, HAS_PROPERTY, etc.) with properties
- [x] Implement temporal (PRECEDES) and spatial (SPATIALLY_RELATES_TO) relationships (**Note:** Basic structure and validation for SPATIALLY_RELATES_TO implemented via API)
- [x] Add constraints to ensure relationships have required properties (**Note:** Application-level validation for `spatial_unit` implemented and tested via API)
- [ ] Add indices for relationship queries
- [x] **Steps to Test**: Create sample relationships between concepts and verify they conform to requirements (Partially done via `POST /relationships` API tests for spatial validation)
- [x] **Steps to Test**: Create sample relationships between concepts and verify they conform to requirements (Partially done via `POST`, `GET`, `PATCH` API tests).

### Task 4: Query Development
- [ ] Develop Cypher queries for retrieving concepts by all four categories
- [ ] Create queries for navigating semantic, temporal, and spatial relationships
- [x] Implement filtering based on confidence and stability (**Note:** Basic `CREATE` and `GET` queries with property handling/filtering implemented in API endpoints)
- [x] **Steps to Test**: Execute sample queries against test data and verify correct results (Partially done via `POST` and `GET` API endpoint tests).
- [x] **Steps to Test**: Execute sample queries against test data and verify correct results (Partially done via `POST`, `GET` (list/detail), `PATCH` API endpoint tests for concepts and relationships).

### Task 5: Documentation and Sample Data
- [ ] Document the entire schema with diagrams, clearly explaining the hybrid approach
- [x] Create sample datasets demonstrating the categorical structure (Done via test fixtures/setup)
- [ ] Write example queries for common usage patterns
- [ ] **Steps to Test**: Have another team member review documentation and successfully run example queries

## 10. Philosophical Considerations

The current implementation takes a pragmatic approach to representing Kant's categorical framework, particularly regarding Quality and Modality. Some philosophical simplifications have been made for implementation feasibility while preserving the intent of Kant's system.

For a detailed discussion of these philosophical considerations, their implications, and our strategy for addressing them in future phases, see:
- [Philosophical Considerations in Kantian Category Implementation](../../design-docs/Philosophical-Considerations-Category-Implementation.md)

## 11. Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Current Date | 1.0 | Initial PRD | AI Assistant |
| Current Date | 1.1 | Updated to clarify Kantian distinction between Categories and General Logic | AI Assistant |
| Current Date | 1.2 | Updated to specify hybrid approach for category representation, added Forms of Intuition (temporal/spatial relationships), and aligned requirements with implementation details | AI Assistant | 