"""
Contains specialized Cypher query constants that were previously loaded from query_templates.cypher
via the cypher_loader utility.
"""

# Get causal chain (path from a concept following CAUSES relationships)
GET_CAUSAL_CHAIN = """
MATCH path = (start:Concept)-[rels:CAUSES*1..{max_depth}]->(effect:Concept)
WHERE elementId(start) = $conceptId
WITH nodes(path) AS path_nodes, relationships(path) AS path_rels
RETURN
    [node IN path_nodes | node {{.*, elementId: elementId(node)}}] AS nodes,
    [rel IN path_rels | rel {{
        elementId: elementId(rel), 
        start_node_id: elementId(startNode(rel)),
        end_node_id: elementId(endNode(rel)),
        type: type(rel),
        properties: properties(rel)
    }}] AS relationships
LIMIT $resultLimit
"""

# Get all relationships for a concept (both incoming and outgoing)
GET_ALL_RELATIONSHIPS_FOR_CONCEPT = """
MATCH (c:Concept)-[r]->(other:Concept)
WHERE elementId(c) = $conceptId
RETURN 
    type(r) AS relationship_type, 
    elementId(other) AS otherId, 
    other.name AS otherName, 
    r.confidence_score AS confidence,
    r AS rel,
    c AS startNode,
    other AS endNode
UNION
MATCH (other:Concept)-[r]->(c:Concept)
WHERE elementId(c) = $conceptId
RETURN 
    type(r) AS relationship_type, 
    elementId(other) AS otherId, 
    other.name AS otherName, 
    r.confidence_score AS confidence,
    r AS rel,
    other AS startNode,
    c AS endNode
ORDER BY relationship_type, otherName
SKIP $skip
LIMIT $limit
"""

# Get concept hierarchy (following CONTAINS relationships)
GET_CONCEPT_HIERARCHY = """
MATCH path = (c:Concept)-[:CONTAINS*1..$maxDepth]->(part:Concept)
WHERE elementId(c) = $conceptId
RETURN path AS p
LIMIT $resultLimit
"""

# Get concept membership (following IS_PART_OF relationships)
GET_CONCEPT_MEMBERSHIP = """
MATCH path = (c:Concept)-[:IS_PART_OF*1..$maxDepth]->(whole:Concept)
WHERE elementId(c) = $conceptId
RETURN path AS p
LIMIT $resultLimit
"""

# Get concepts interacting with a given concept (INTERACTS_WITH relationships)
GET_INTERACTING_CONCEPTS = """
MATCH (c:Concept)-[r:INTERACTS_WITH]-(other:Concept)
WHERE elementId(c) = $conceptId
RETURN other { .*, elementId: elementId(other) } AS interactingConcept, 
       r.confidence_score AS confidence
ORDER BY r.confidence_score DESC
LIMIT $limit
"""

# Get concepts by quality
GET_CONCEPTS_BY_QUALITY = """
MATCH (c:Concept)
WHERE c.quality = $quality
RETURN c { .*, elementId: elementId(c) } AS concept
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

# Get concepts by modality
GET_CONCEPTS_BY_MODALITY = """
MATCH (c:Concept)
WHERE c.modality = $modality
RETURN c { .*, elementId: elementId(c) } AS concept
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

# Get temporal relationships
GET_TEMPORAL_RELATIONSHIPS = """
MATCH (c:Concept)-[r:PRECEDES]->(after:Concept)
WHERE elementId(c) = $conceptId
RETURN 
    after { .*, elementId: elementId(after) } AS relatedConcept,
    r AS rel,
    c AS startNode,
    after AS endNode,
    r.temporal_distance AS temporalDistance, 
    r.confidence_score AS confidence
UNION
MATCH (before:Concept)-[r:PRECEDES]->(c:Concept)
WHERE elementId(c) = $conceptId
RETURN 
    before { .*, elementId: elementId(before) } AS relatedConcept,
    r AS rel,
    before AS startNode,
    c AS endNode,
    r.temporal_distance AS temporalDistance, 
    r.confidence_score AS confidence
ORDER BY confidence DESC
LIMIT $limit
"""

# Get spatial relationships
GET_SPATIAL_RELATIONSHIPS = """
MATCH (c:Concept)-[r:SPATIALLY_RELATES_TO]-(other:Concept)
WHERE elementId(c) = $conceptId
RETURN 
    other { .*, elementId: elementId(other) } AS relatedConcept,
    r AS rel,
    CASE WHEN startNode(r) = c THEN c ELSE other END AS startNode,
    CASE WHEN endNode(r) = c THEN other ELSE c END AS endNode,
    r.relation_type AS relationType, 
    r.distance AS distance, 
    r.confidence_score AS confidence
ORDER BY confidence DESC
LIMIT $limit
""" 