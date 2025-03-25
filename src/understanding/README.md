# Kantian Category Structure Knowledge Graph

This directory contains the Neo4j implementation of the Kantian Category Structure Knowledge Graph, which serves as the foundation for the Understanding Module of the KantAI backend system.

## Overview

The implementation creates a graph database schema based on Kant's categorical framework, organizing knowledge according to the four primary Kantian categories: Quantity, Quality, Relation, and Modality. Each category is further divided into three subcategories, forming the conceptual foundation for the knowledge representation.

## Directory Structure

```
src/understanding/
  ├── schema/                # Database schema definitions
  │   ├── category_structure.cypher   # Category and subcategory nodes
  │   ├── concept_structure.cypher    # Concept node structure and constraints
  │   └── relationship_types.cypher   # Relationship type definitions
  ├── queries/               # Reusable query templates
  │   └── query_templates.cypher      # APOC stored procedures
  ├── examples/              # Example data for demonstration
  │   └── sample_concepts.cypher      # Sample concepts and relationships
  └── tests/                 # Test scripts
      └── validation_queries.cypher   # Queries to validate implementation
```

## Implementation Details

### Categories and Subcategories

The implementation creates four main Category nodes representing Kant's primary categories:

1. **Quantity**: Deals with the extension of concepts
   - Unity: Concept of One
   - Plurality: Concept of Many
   - Totality: Concept of All

2. **Quality**: Deals with the content of concepts
   - Reality: Positive determination
   - Negation: Negative determination
   - Limitation: Bounded determination

3. **Relation**: Deals with how concepts relate to each other
   - Substance-Accident: Relation of inherence and subsistence
   - Causality: Relation of cause and effect
   - Community: Reciprocal relation between agent and patient

4. **Modality**: Deals with the relation of concepts to the faculty of cognition
   - Possibility/Impossibility: Agreement or conflict with conditions of experience
   - Existence/Non-existence: Agreement or conflict with material conditions of experience
   - Necessity/Contingency: Agreement or determination by material conditions of experience

### Concept Structure

Concept nodes represent the entities within the knowledge graph and have the following properties:

- **id**: UUID - unique identifier for the concept
- **name**: String - name of the concept
- **description**: String - description of the concept
- **confidence_score**: Float (0.0-1.0) - confidence in the concept
- **stability_status**: String ("ephemeral" or "stable") - stability of the concept
- **source_information**: String - source of the concept
- **creation_timestamp**: DateTime - when the concept was created
- **quality**: String (optional) - Quality category: "Reality", "Negation", or "Limitation"
- **modality**: String (optional) - Modality category: "Possible", "Actual", or "Necessary"

### Unity Representation

Unity, a subcategory under Quantity, is implicitly embodied in individual Concept nodes. In Kant's system, Unity represents the concept of "One" - a singular entity. In our implementation:

- Each individual Concept node inherently represents a unity (a single entity)
- When using the INSTANCE_OF relationship to connect a concept to a type (e.g., "Tree_1" to "Tree"), we're creating a specific instance (Unity) of a general concept
- Concrete examples in our system include concepts like "Ball", "Earth", and "Lightning" that represent singular entities

This approach to Unity contrasts with Plurality (represented by relationships like IS_PART_OF) and Totality (represented by relationships like CONTAINS), which explicitly connect multiple concepts.

### Quality and Modality Properties

Unlike the other categories that are primarily implemented through relationships between concepts, Quality and Modality are implemented as properties on the Concept nodes themselves:

- **Quality Property**: Directly captures the Quality aspect of a concept
  - "Reality": Positive determination (e.g., "Red", "Ball", "Earth")
  - "Negation": Negative determination (e.g., "Absence", "Non-existence")
  - "Limitation": Bounded determination (e.g., "Horizon", boundary concepts)

- **Modality Property**: Captures the modal status of a concept
  - "Possible": Concepts that could exist (e.g., "Unicorn")
  - "Actual": Concepts that do exist (e.g., "Ball", "Earth")
  - "Necessary": Concepts that must exist (e.g., "Gravity", "Mathematics")

These properties are constrained to ensure they only accept valid values aligned with Kant's framework.

### Relationship Types

The implementation includes relationship types that correspond to Kant's categories:

- **INSTANCE_OF**: Connects concepts to their categorical classification
- **HAS_PROPERTY**: Implements Substance-Accident relationships
- **CAUSES**: Implements Causality relationships
- **INTERACTS_WITH**: Implements Community (reciprocal) relationships
- **CONTAINS**: Implements Totality relationships
- **IS_PART_OF**: Implements Plurality relationships

Additionally, we've implemented extended relationship types for enhanced expressivity:

- **PRECEDES**: Implements temporal relationships with properties:
  - temporal_distance: Description of time between concepts
  - temporal_unit: Unit of time measurement
  - temporal_order: For sequences with multiple events

- **SPATIALLY_RELATES_TO**: Implements spatial relationships with properties:
  - relation_type: Type of spatial relationship (contains, adjacent, orbits)
  - distance: Measurement between concepts
  - spatial_unit: Unit of spatial measurement
  - spatial_dimension: Dimension in which the relationship occurs

### Query Templates

The implementation includes APOC stored procedures for common queries, optimized for scale:

- **getConceptsByCategory**: Retrieves concepts under a specified category
- **getConceptsBySubcategory**: Retrieves concepts under a specific subcategory
- **getCausalChain**: Gets a chain of causal relationships with depth limits
- **getConceptProperties**: Retrieves properties of a concept
- **getConceptsByConfidence**: Filters concepts by confidence threshold
- **getAllRelationshipsForConcept**: Gets all relationships for a concept with pagination
- **getConceptHierarchy**: Retrieves totality relationships with depth limits
- **getConceptMembership**: Retrieves plurality relationships with depth limits
- **getInteractingConcepts**: Gets concepts in reciprocal relationships

New query templates for Quality, Modality, and extended relationships:

- **getConceptsByQuality**: Retrieves concepts with a specific Quality value
- **getConceptsByModality**: Retrieves concepts with a specific Modality value
- **getTemporalRelationships**: Gets temporal relationships for a concept
- **getSpatialRelationships**: Gets spatial relationships for a concept

## Usage

### Setting Up the Database

1. Start Neo4j with APOC plugins enabled:

```bash
docker run \
  --name kantai-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -e NEO4JLABS_PLUGINS=["apoc", "graph-data-science", "n10s"] \
  neo4j:latest
```

2. Initialize the database schema:

```bash
cat schema/category_structure.cypher schema/concept_structure.cypher schema/relationship_types.cypher | cypher-shell -u neo4j -p password
```

3. Load sample data (optional):

```bash
cat examples/sample_concepts.cypher | cypher-shell -u neo4j -p password
```

4. Register query templates:

```bash
cat queries/query_templates.cypher | cypher-shell -u neo4j -p password
```

5. Validate the implementation:

```bash
cat tests/validation_queries.cypher | cypher-shell -u neo4j -p password
```

## Examples

### Creating a Concept with Quality and Modality

```cypher
CREATE (concept:Concept {
  id: apoc.create.uuid(), 
  name: "ExampleConcept", 
  description: "An example concept for demonstration",
  confidence_score: 0.8,
  stability_status: "ephemeral",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
})
```

### Classifying a Concept

```cypher
MATCH (concept:Concept {name: "ExampleConcept"})
MATCH (subcategory:Subcategory {name: "Unity"})
CREATE (concept)-[:INSTANCE_OF {
  confidence_score: 0.9,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(subcategory)
```

### Creating a Temporal Relationship

```cypher
MATCH (concept1:Concept {name: "Lightning"})
MATCH (concept2:Concept {name: "Thunder"})
CREATE (concept1)-[:PRECEDES {
  confidence_score: 0.95,
  creation_timestamp: datetime(),
  source_information: "manual entry",
  temporal_distance: "seconds",
  temporal_unit: "seconds",
  temporal_order: 1
}]->(concept2)
```

### Creating a Spatial Relationship

```cypher
MATCH (concept1:Concept {name: "Earth"})
MATCH (concept2:Concept {name: "Moon"})
CREATE (concept1)-[:SPATIALLY_RELATES_TO {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry",
  relation_type: "orbits",
  distance: "384,400",
  spatial_unit: "km",
  spatial_dimension: "3D"
}]->(concept2)
```

### Querying Concepts by Quality

```cypher
CALL custom.getConceptsByQuality("Reality", 0, 100) YIELD id, name, description
RETURN name, description
```

### Querying Concepts by Modality

```cypher
CALL custom.getConceptsByModality("Possible", 0, 100) YIELD id, name, description
RETURN name, description
```

### Querying Temporal and Spatial Relationships

```cypher
// Get all temporal relationships for a concept
MATCH (c:Concept {name: "Lightning"})
CALL custom.getTemporalRelationships(c.id, 50) YIELD name, temporalDistance
RETURN name, temporalDistance

// Get all spatial relationships for a concept
MATCH (c:Concept {name: "Earth"})
CALL custom.getSpatialRelationships(c.id, 50) YIELD name, relationType, distance
RETURN name, relationType, distance
```

## Performance Considerations

The implementation includes several optimizations for scale:

- Default depth limitations on recursive queries (e.g., getCausalChain)
- Result limiting to prevent excessive data retrieval
- Pagination support for high-volume queries
- Indices on commonly queried properties
- Ordering to ensure consistent results

## Future Extensions

- Integration with SHACL constraints for more sophisticated validation
- Addition of versioning support for evolving concepts
- Implementation of multi-language concept representation
- Integration with external ontologies and knowledge bases
- Advanced query caching and path optimization
- Extension of spatial and temporal relationship types
- Development of advanced visualization capabilities 