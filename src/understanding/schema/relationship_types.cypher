// Relationship Types - Neo4j Implementation
// This file defines the relationship types based on Kant's categorical framework

// Standard properties for all relationship types
/*
All relationships should have the following properties:
- confidence_score: Float (0.0-1.0) - confidence in the relationship
- creation_timestamp: DateTime - when the relationship was created
- source_information: String - source of the relationship information
- other optional properties depending on the relationship type
*/

// Define INSTANCE_OF relationship type
// INSTANCE_OF connects concepts to their categorical classification
// Example: (Ball)-[:INSTANCE_OF]->(Substance-Accident)

// Define HAS_PROPERTY relationship type
// HAS_PROPERTY implements Substance-Accident relationships
// Example: (Ball)-[:HAS_PROPERTY]->(Red)

// Define CAUSES relationship type
// CAUSES implements Causality relationships
// Example: (Heat)-[:CAUSES]->(Expansion)

// Define INTERACTS_WITH relationship type
// INTERACTS_WITH implements Community (reciprocal) relationships
// Example: (Earth)-[:INTERACTS_WITH]->(Moon)

// Define CONTAINS relationship type
// CONTAINS implements Totality relationships
// Example: (Forest)-[:CONTAINS]->(Tree)

// Define IS_PART_OF relationship type
// IS_PART_OF implements Plurality relationships
// Example: (Tree)-[:IS_PART_OF]->(Forest)

// Extended relationship types for enhanced expressivity

// Define PRECEDES relationship type
// PRECEDES implements temporal relationships between concepts
// Example: (Lightning)-[:PRECEDES {temporal_distance: "seconds"}]->(Thunder)
// Properties:
// - temporal_distance: String - description of the time between concepts
// - temporal_unit: String - unit of time measurement (seconds, minutes, years, etc.)
// - temporal_order: Integer - for establishing sequences of more than two events

// Define SPATIALLY_RELATES_TO relationship type
// SPATIALLY_RELATES_TO implements spatial relationships between concepts
// Example: (Earth)-[:SPATIALLY_RELATES_TO {relation_type: "orbits", distance: "384400 km"}]->(Moon)
// Properties:
// - relation_type: String - type of spatial relationship (contains, adjacent, orbits, etc.)
// - distance: String - description of the distance between concepts
// - spatial_unit: String - unit of spatial measurement (mm, km, light-years, etc.)
// - spatial_dimension: String - dimension in which the relationship occurs (1D, 2D, 3D)

// Optional: Create relationship property existence constraints
// This ensures that all relationships have the required properties
CREATE CONSTRAINT rel_confidence_exists IF NOT EXISTS 
FOR ()-[r:INSTANCE_OF]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT rel_timestamp_exists IF NOT EXISTS 
FOR ()-[r:INSTANCE_OF]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT hasprop_confidence_exists IF NOT EXISTS 
FOR ()-[r:HAS_PROPERTY]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT hasprop_timestamp_exists IF NOT EXISTS 
FOR ()-[r:HAS_PROPERTY]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT causes_confidence_exists IF NOT EXISTS 
FOR ()-[r:CAUSES]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT causes_timestamp_exists IF NOT EXISTS 
FOR ()-[r:CAUSES]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT interacts_confidence_exists IF NOT EXISTS 
FOR ()-[r:INTERACTS_WITH]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT interacts_timestamp_exists IF NOT EXISTS 
FOR ()-[r:INTERACTS_WITH]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT contains_confidence_exists IF NOT EXISTS 
FOR ()-[r:CONTAINS]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT contains_timestamp_exists IF NOT EXISTS 
FOR ()-[r:CONTAINS]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT ispart_confidence_exists IF NOT EXISTS 
FOR ()-[r:IS_PART_OF]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT ispart_timestamp_exists IF NOT EXISTS 
FOR ()-[r:IS_PART_OF]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

// Constraints for extended relationship types
CREATE CONSTRAINT precedes_confidence_exists IF NOT EXISTS 
FOR ()-[r:PRECEDES]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT precedes_timestamp_exists IF NOT EXISTS 
FOR ()-[r:PRECEDES]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT precedes_temporal_distance_exists IF NOT EXISTS 
FOR ()-[r:PRECEDES]->() 
REQUIRE r.temporal_distance IS NOT NULL;

CREATE CONSTRAINT spatial_confidence_exists IF NOT EXISTS 
FOR ()-[r:SPATIALLY_RELATES_TO]->() 
REQUIRE r.confidence_score IS NOT NULL;

CREATE CONSTRAINT spatial_timestamp_exists IF NOT EXISTS 
FOR ()-[r:SPATIALLY_RELATES_TO]->() 
REQUIRE r.creation_timestamp IS NOT NULL;

CREATE CONSTRAINT spatial_relation_type_exists IF NOT EXISTS 
FOR ()-[r:SPATIALLY_RELATES_TO]->() 
REQUIRE r.relation_type IS NOT NULL; 