"""
Contains Cypher query constants for Concept CRUD operations.
"""

# Create Concept
CREATE_CONCEPT = """
CREATE (c:Concept {
    name: $name,
    description: $description,
    quality: $quality,
    modality: $modality,
    stability: $stability,
    confidence_score: $confidence_score,
    created_at: datetime(),
    updated_at: datetime()
 })
 RETURN c { .*, elementId: elementId(c) } AS c
"""

# Get Concept By Element ID
GET_CONCEPT_BY_ID = """
MATCH (c:Concept)
WHERE elementId(c) = $element_id
RETURN c { .*, elementId: elementId(c) } AS c
"""

# Update Concept Partially
UPDATE_CONCEPT_PARTIAL = """
MATCH (c:Concept)
WHERE elementId(c) = $element_id
SET c += $update_data, c.updated_at = datetime()
RETURN c { .*, elementId: elementId(c) } AS c
"""

# Delete Concept By Element ID
DELETE_CONCEPT = """
MATCH (c:Concept)
WHERE elementId(c) = $element_id
DETACH DELETE c
RETURN count(c) AS deleted_count
"""

# Note: Queries previously loaded from query_templates.cypher via APOC names
# could also be migrated here if we decide to move away from the loader entirely.
# For now, only adding the ones that were causing issues.
GET_CONCEPTS = """
MATCH (concept:Concept)
RETURN concept { .*, elementId: elementId(concept) } AS concept
ORDER BY concept.name
SKIP $skip
LIMIT $limit
"""

GET_CONCEPTS_BY_CATEGORY = """
MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category {name: $category})
RETURN c { .*, elementId: elementId(c) } AS concept // Alias as concept for consistency
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

GET_CONCEPTS_BY_SUBCATEGORY = """
MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory {name: $subcategory})
RETURN c { .*, elementId: elementId(c) } AS concept // Alias as concept
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

GET_CONCEPTS_BY_CONFIDENCE = """
MATCH (c:Concept) 
WHERE c.confidence_score >= $threshold
RETURN c { .*, elementId: elementId(c) } AS concept // Alias as concept
ORDER BY c.confidence_score DESC
LIMIT $limit 
// Note: SKIP might be needed here too depending on desired pagination
"""

GET_CONCEPT_PROPERTIES = """
MATCH (c:Concept)-[r:HAS_PROPERTY]->(prop:Concept)
WHERE elementId(c) = $conceptId
RETURN prop { .*, elementId: elementId(prop) } AS prop // Return full property node
ORDER BY r.confidence_score DESC
LIMIT $limit
"""

# Add other queries as needed...
