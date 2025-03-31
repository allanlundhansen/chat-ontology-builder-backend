"""
Contains Cypher query constants for Relationship CRUD operations.
"""

# List Relationships (with optional type filtering)
LIST_RELATIONSHIPS = """
MATCH (source)-[rel]->(target)
{where_clause}
RETURN
    elementId(rel) AS elementId,
    elementId(source) AS source_id,
    source.name AS source_name,
    elementId(target) AS target_id,
    target.name AS target_name,
    type(rel) AS type,
    properties(rel) AS properties
ORDER BY properties(rel).created_at DESC
SKIP $skip
LIMIT $limit
"""

# Count Relationships (for pagination)
COUNT_RELATIONSHIPS = """
MATCH (source)-[rel]->(target)
{where_clause}
RETURN count(rel) AS total_count
"""

# Create Relationship
CREATE_RELATIONSHIP = """
MATCH (source) WHERE elementId(source) = $source_id
MATCH (target) WHERE elementId(target) = $target_id
CREATE (source)-[rel:`{rel_type}`]->(target)
SET rel = $properties
RETURN
    elementId(rel) AS elementId,
    elementId(source) AS source_id,
    source.name AS source_name,
    elementId(target) AS target_id,
    target.name AS target_name,
    type(rel) AS type,
    properties(rel) AS properties
"""

# Check if Node Exists
CHECK_NODE_EXISTS = """
MATCH (n) WHERE elementId(n) = $id 
RETURN count(n) > 0 AS exists
"""

# Get Relationship by Element ID
GET_RELATIONSHIP_BY_ID = """
MATCH (source)-[r]->(target)
WHERE elementId(r) = $element_id
RETURN 
    elementId(r) AS elementId,
    type(r) AS type,
    properties(r) AS properties,
    elementId(source) AS source_id,
    source.name AS source_name,
    elementId(target) AS target_id,
    target.name AS target_name
"""

# Update Relationship (PATCH)
UPDATE_RELATIONSHIP = """
MATCH (source)-[r]->(target)
WHERE elementId(r) = $element_id
WITH r, source, target, type(r) as current_type
{set_statement}
RETURN
    elementId(r) AS elementId,
    elementId(source) AS source_id,
    source.name AS source_name,
    elementId(target) AS target_id,
    target.name AS target_name,
    type(r) AS type,
    properties(r) AS properties
"""

# Check if Relationship Exists
CHECK_RELATIONSHIP_EXISTS = """
MATCH ()-[r]-() 
WHERE elementId(r) = $element_id 
RETURN count(r) > 0 AS exists
"""

# Delete Relationship
DELETE_RELATIONSHIP = """
MATCH ()-[r]-() 
WHERE elementId(r) = $element_id 
DETACH DELETE r
"""
