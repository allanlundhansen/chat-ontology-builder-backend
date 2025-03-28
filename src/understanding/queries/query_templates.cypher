// Query Templates - Neo4j Implementation
// This file contains reusable Cypher query templates for working with the Kantian knowledge graph

// Using APOC procedures for stored queries (if APOC is available)
// Otherwise, these can be used as query templates in the application

// Get concepts by category - corrected to match through subcategories
// Optimized with pagination and default limits for scale
CALL apoc.custom.asProcedure(
  'getConceptsByCategory',
  'MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category {name: $category})
   RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
   ORDER BY c.name
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['category', 'STRING'], ['skip', 'INTEGER'], ['limit', 'INTEGER']], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get concepts by subcategory
// Optimized with pagination and default limits for scale
CALL apoc.custom.asProcedure(
  'getConceptsBySubcategory',
  'MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory {name: $subcategory})
   RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
   ORDER BY c.name
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['subcategory', 'STRING'], ['skip', 'INTEGER'], ['limit', 'INTEGER']], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get causal chain
// Optimized with explicit default max_depth and result limit
CALL apoc.custom.asProcedure(
  'getCausalChain',
  'MATCH path = (start:Concept {id: $conceptId})-[:CAUSES*1..$maxDepth]->(effect:Concept)
   RETURN path
   LIMIT $resultLimit',
  'READ',
  [['conceptId', 'STRING'], ['maxDepth', 'INTEGER', 3], ['resultLimit', 'INTEGER', 100]], 
  [['path', 'PATH']]
);

// Get properties of a concept (substance-accident relationships)
CALL apoc.custom.asProcedure(
  'getConceptProperties',
  'MATCH (c:Concept {id: $conceptId})-[r:HAS_PROPERTY]->(prop:Concept)
   RETURN prop.id AS id, prop.name AS name, prop.description AS description, r.confidence_score AS confidence
   ORDER BY r.confidence_score DESC
   LIMIT $limit',
  'READ',
  [['conceptId', 'STRING'], ['limit', 'INTEGER', 50]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get concepts above confidence threshold
CALL apoc.custom.asProcedure(
  'getConceptsByConfidence',
  'MATCH (c:Concept) 
   WHERE c.confidence_score >= $threshold
   RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
   ORDER BY c.confidence_score DESC
   LIMIT $limit',
  'READ',
  [['threshold', 'FLOAT'], ['limit', 'INTEGER', 100]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get all relationships for a concept
// Optimized to return limited and paginated results
CALL apoc.custom.asProcedure(
  'getAllRelationshipsForConcept',
  'MATCH (c:Concept {id: $conceptId})-[r]->(other:Concept)
   RETURN type(r) AS relationship_type, other.id AS otherId, other.name AS otherName, 
          r.confidence_score AS confidence
   UNION
   MATCH (other:Concept)-[r]->(c:Concept {id: $conceptId})
   RETURN type(r) AS relationship_type, other.id AS otherId, other.name AS otherName, 
          r.confidence_score AS confidence
   ORDER BY relationship_type, otherName
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['conceptId', 'STRING'], ['skip', 'INTEGER', 0], ['limit', 'INTEGER', 50]], 
  [['relationship_type', 'STRING'], ['otherId', 'STRING'], ['otherName', 'STRING'], ['confidence', 'FLOAT']]
);

// Get concept hierarchy (totality relationships)
// Optimized with max_depth parameter and limit
CALL apoc.custom.asProcedure(
  'getConceptHierarchy',
  'MATCH path = (c:Concept {id: $conceptId})-[:CONTAINS*1..$maxDepth]->(part:Concept)
   RETURN path
   LIMIT $resultLimit',
  'READ',
  [['conceptId', 'STRING'], ['maxDepth', 'INTEGER', 3], ['resultLimit', 'INTEGER', 100]], 
  [['path', 'PATH']]
);

// Get concept membership (plurality relationships)
// Optimized with max_depth parameter and limit
CALL apoc.custom.asProcedure(
  'getConceptMembership',
  'MATCH path = (c:Concept {id: $conceptId})-[:IS_PART_OF*1..$maxDepth]->(whole:Concept)
   RETURN path
   LIMIT $resultLimit',
  'READ',
  [['conceptId', 'STRING'], ['maxDepth', 'INTEGER', 3], ['resultLimit', 'INTEGER', 100]], 
  [['path', 'PATH']]
);

// Get concepts interacting with a given concept (community relationships)
CALL apoc.custom.asProcedure(
  'getInteractingConcepts',
  'MATCH (c:Concept {id: $conceptId})-[r:INTERACTS_WITH]-(other:Concept)
   RETURN other.id AS id, other.name AS name, other.description AS description, r.confidence_score AS confidence
   ORDER BY r.confidence_score DESC
   LIMIT $limit',
  'READ',
  [['conceptId', 'STRING'], ['limit', 'INTEGER', 50]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// New query templates for Quality and Modality properties

// Get concepts by quality
CALL apoc.custom.asProcedure(
  'getConceptsByQuality',
  'MATCH (c:Concept)
   WHERE c.quality = $quality
   RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
   ORDER BY c.name
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['quality', 'STRING'], ['skip', 'INTEGER', 0], ['limit', 'INTEGER', 50]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get concepts by modality
CALL apoc.custom.asProcedure(
  'getConceptsByModality',
  'MATCH (c:Concept)
   WHERE c.modality = $modality
   RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
   ORDER BY c.name
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['modality', 'STRING'], ['skip', 'INTEGER', 0], ['limit', 'INTEGER', 50]],
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], ['confidence', 'FLOAT']]
);

// Get concepts (basic listing with pagination)
// Needed for the root GET /api/v1/concepts endpoint without filters
CALL apoc.custom.asProcedure(
  'getConcepts',
  'MATCH (concept:Concept)
   RETURN concept
   ORDER BY concept.name
   SKIP $skip
   LIMIT $limit',
  'READ',
  [['skip', 'INTEGER', 0], ['limit', 'INTEGER', 50]],
  [['concept', 'NODE']]
);

// Note on Hybrid Approach:
// The queries reflect the hybrid approach to Kantian category representation:
// 1. Quality and Modality categories use direct property queries (getConceptsByQuality, getConceptsByModality)
// 2. Quantity and Relation categories use relationship-based queries (getConceptsByCategory, getConceptsBySubcategory)
// 3. Temporal and spatial relationships (Forms of Intuition) have dedicated query templates 

// New query templates for temporal and spatial relationships

// Get temporal relationships (precedes)
CALL apoc.custom.asProcedure(
  'getTemporalRelationships',
  'MATCH (c:Concept {id: $conceptId})-[r:PRECEDES]->(after:Concept)
   RETURN after.id AS id, after.name AS name, after.description AS description, 
          r.temporal_distance AS temporalDistance, r.confidence_score AS confidence
   UNION
   MATCH (before:Concept)-[r:PRECEDES]->(c:Concept {id: $conceptId})
   RETURN before.id AS id, before.name AS name, before.description AS description, 
          r.temporal_distance AS temporalDistance, r.confidence_score AS confidence
   ORDER BY confidence DESC
   LIMIT $limit',
  'READ',
  [['conceptId', 'STRING'], ['limit', 'INTEGER', 50]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], 
   ['temporalDistance', 'STRING'], ['confidence', 'FLOAT']]
);

// Get spatial relationships
CALL apoc.custom.asProcedure(
  'getSpatialRelationships',
  'MATCH (c:Concept {id: $conceptId})-[r:SPATIALLY_RELATES_TO]-(other:Concept)
   RETURN other.id AS id, other.name AS name, other.description AS description,
          r.relation_type AS relationType, r.distance AS distance, r.confidence_score AS confidence
   ORDER BY confidence DESC
   LIMIT $limit',
  'READ',
  [['conceptId', 'STRING'], ['limit', 'INTEGER', 50]], 
  [['id', 'STRING'], ['name', 'STRING'], ['description', 'STRING'], 
   ['relationType', 'STRING'], ['distance', 'STRING'], ['confidence', 'FLOAT']]
); 