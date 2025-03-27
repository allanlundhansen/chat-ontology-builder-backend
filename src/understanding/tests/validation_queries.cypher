// Validation Queries - Neo4j Implementation
// This file contains test queries to validate the Kantian knowledge graph implementation

// Test 1: Verify Category and Subcategory Counts
// Ensure the 4 main categories and their 3 subcategories each exist
MATCH (c:Category)
OPTIONAL MATCH (c)-[:HAS_SUBCATEGORY]->(sub:Subcategory)
RETURN c.name AS Category, count(sub) AS SubcategoryCount
ORDER BY c.name;

// Expected: 4 rows (Modality, Quality, Quantity, Relation), each with SubcategoryCount = 3

// Test 2: Verify subcategories are connected to the correct categories
MATCH (c:Category)-[:HAS_SUBCATEGORY]->(s:Subcategory)
RETURN c.name AS Category, collect(s.name) AS Subcategories;

// Test 3: Verify concept classifications
// This query checks that concepts are correctly classified within the categorical framework
MATCH (concept:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category)
RETURN concept.name AS Concept, sub.name AS Subcategory, cat.name AS Category;

// Test 4: Verify relationship types
// This query counts the number of each relationship type
MATCH (c1:Concept)-[r]->(c2:Concept)
WHERE type(r) <> "INSTANCE_OF"
RETURN type(r) AS RelationshipType, count(r) AS Count;

// Test 5: Test the getConceptsByCategory logic (formerly procedure)
// This tests the corrected query that matches through subcategories
// Replaces: CALL getConceptsByCategory("Relation", 0, 10) YIELD ...
WITH "Relation" AS category
MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category {name: category})
RETURN c.name AS name, c.description AS description, c.confidence_score AS confidence
ORDER BY c.name
SKIP 0
LIMIT 10;

// Test 6: Test the getCausalChain logic (formerly procedure)
// Replaces: CALL getCausalChain(heatId, 3, 10) YIELD path
MATCH (c:Concept {name: "Heat"})
WITH c.id AS conceptId
MATCH path = (start:Concept {id: conceptId})-[:CAUSES*1..3]->(effect:Concept)
RETURN path
LIMIT 10;

// Test 7: Test getConceptProperties logic (formerly procedure)
// Replaces: CALL getConceptProperties(ballId, 10) YIELD ...
MATCH (c:Concept {name: "Ball"})
WITH c.id AS conceptId
MATCH (concept:Concept {id: conceptId})-[r:HAS_PROPERTY]->(prop:Concept)
RETURN prop.name AS name, prop.description AS description, r.confidence_score AS confidence
ORDER BY r.confidence_score DESC
LIMIT 10;

// Test 8: Test integrity constraints
// This checks that all relationships have the required properties
MATCH ()-[r:INSTANCE_OF]->()
WHERE r.confidence_score IS NULL OR r.creation_timestamp IS NULL
RETURN count(r) AS MissingPropertiesCount;

// Test 9: Test relationship between Quantity subcategories and related concepts
MATCH (cat:Category {name: "Quantity"})-[:HAS_SUBCATEGORY]->(sub:Subcategory)<-[:INSTANCE_OF]-(c:Concept)
RETURN sub.name AS QuantitySubcategory, collect(c.name) AS Concepts;

// Test 10: Verify reciprocal community relationships
MATCH (c1:Concept)-[:INTERACTS_WITH]->(c2:Concept)
WHERE NOT exists((c2)-[:INTERACTS_WITH]->(c1))
RETURN c1.name AS Concept1, c2.name AS Concept2, "Missing reciprocal relationship" AS Issue;

// Test 11: Verify Quality property values
// This checks that all concepts with Quality property have valid values
MATCH (c:Concept)
WHERE c.quality IS NOT NULL
  AND NOT (c.quality IN ["Reality", "Negation", "Limitation"])
RETURN c.name AS Concept, c.quality AS InvalidQualityValue;

// Test 12: Verify Modality property values
// This checks that all concepts with Modality property have valid values
MATCH (c:Concept)
WHERE c.modality IS NOT NULL
  AND NOT (c.modality IN ["Possibility/Impossibility", "Existence/Non-existence", "Necessity/Contingency"])
RETURN c.name AS Concept, c.modality AS InvalidModalityValue;

// Test 13: Count concepts by Quality
// Shows distribution of concepts across Quality categories
MATCH (c:Concept)
WHERE c.quality IS NOT NULL
RETURN c.quality AS Quality, count(c) AS ConceptCount
ORDER BY ConceptCount DESC;

// Test 14: Count concepts by Modality
// Shows distribution of concepts across Modality categories
MATCH (c:Concept)
WHERE c.modality IS NOT NULL
RETURN c.modality AS Modality, count(c) AS ConceptCount
ORDER BY ConceptCount DESC;

// Test 15: Verify temporal relationships
// Checks that all PRECEDES relationships have required properties
MATCH (c1:Concept)-[r:PRECEDES]->(c2:Concept)
RETURN c1.name AS From, c2.name AS To, r.temporal_distance AS TemporalDistance,
       r.temporal_unit AS TemporalUnit, r.temporal_order AS TemporalOrder;

// Test 16: Verify spatial relationships
// Checks that all SPATIALLY_RELATES_TO relationships have required properties
MATCH (c1:Concept)-[r:SPATIALLY_RELATES_TO]->(c2:Concept)
RETURN c1.name AS From, c2.name AS To, r.relation_type AS RelationType,
       r.distance AS Distance, r.spatial_unit AS SpatialUnit,
       r.spatial_dimension AS SpatialDimension;

// Test 17: Test getConceptsByQuality logic (formerly procedure)
// Replaces: CALL getConceptsByQuality("Reality", 0, 10) YIELD ...
WITH "Reality" AS quality
MATCH (c:Concept)
WHERE c.quality = quality
RETURN c.name AS name, c.description AS description, c.confidence_score AS confidence
ORDER BY c.name
SKIP 0
LIMIT 10;

// Test 18: Test getConceptsByModality logic (formerly procedure)
// Replaces: CALL getConceptsByModality("Possibility/Impossibility", 0, 10) YIELD ...
WITH "Possibility/Impossibility" AS modality
MATCH (c:Concept)
WHERE c.modality = modality
RETURN c.name AS name, c.description AS description, c.confidence_score AS confidence
ORDER BY c.name
SKIP 0
LIMIT 10;

// Test 19: Test getTemporalRelationships logic (formerly procedure)
// Replaces: CALL getTemporalRelationships(conceptId, 10) YIELD ...

// Branch 1: Relationships originating FROM "Lightning"
MATCH (c:Concept {name: "Lightning"}) // Find the starting concept
MATCH (c)-[r:PRECEDES]->(after:Concept)
RETURN after.name AS name, after.description AS description,
       r.temporal_distance AS temporalDistance, r.confidence_score AS confidence

UNION

// Branch 2: Relationships pointing TO "Lightning"
MATCH (c:Concept {name: "Lightning"}) // Re-find the starting concept
MATCH (before:Concept)-[r:PRECEDES]->(c)
RETURN before.name AS name, before.description AS description,
       r.temporal_distance AS temporalDistance, r.confidence_score AS confidence

// ORDER BY and LIMIT apply to the combined result set
ORDER BY confidence DESC
LIMIT 10;

// Test 20: Test getSpatialRelationships logic (formerly procedure)
// Replaces: CALL getSpatialRelationships(conceptId, 10) YIELD ...
MATCH (c:Concept {name: "Earth"})
WITH c.id AS conceptId
MATCH (concept:Concept {id: conceptId})-[r:SPATIALLY_RELATES_TO]-(other:Concept)
RETURN other.name AS name, other.description AS description,
       r.relation_type AS relationType, r.distance AS distance, r.confidence_score AS confidence
ORDER BY confidence DESC
LIMIT 10;

// Note on Temporal and Spatial Relationships:
// PRECEDES and SPATIALLY_RELATES_TO relationships represent Kant's Forms of Intuition (Time and Space),
// which are not part of the Categories of Understanding but provide the necessary framework for organizing
// experience. These relationships extend the core categorical structure with temporal and spatial dimensions. 