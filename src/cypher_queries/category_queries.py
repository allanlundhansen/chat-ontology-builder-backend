"""
Contains Cypher query constants for Category CRUD operations.
"""

# List all categories and subcategories
LIST_CATEGORIES = """
MATCH (cat:Category)
OPTIONAL MATCH (cat)-[:HAS_SUBCATEGORY]->(sub:Subcategory)
WITH cat, elementId(cat) as cat_elementId, cat.name as cat_name, cat.description as cat_description,
     CASE WHEN sub IS NOT NULL THEN {
         elementId: elementId(sub),
         name: sub.name,
         description: sub.description
     } ELSE NULL END as sub_data
ORDER BY cat.name, sub.name
RETURN
    cat_elementId,
    cat_name,
    cat_description,
    collect(sub_data) as subcategories_data
ORDER BY cat_name
"""

# Get a specific category by name, or get the parent category if a subcategory name is provided
GET_CATEGORY_BY_NAME = """
MATCH (n) WHERE n.name = $name AND (n:Category OR n:Subcategory)
OPTIONAL MATCH (parent_cat:Category)-[:HAS_SUBCATEGORY]->(n) WHERE n:Subcategory
WITH COALESCE(parent_cat, CASE WHEN n:Category THEN n ELSE NULL END) as finalCat
WHERE finalCat IS NOT NULL
MATCH (cat:Category) WHERE elementId(cat) = elementId(finalCat)
OPTIONAL MATCH (cat)-[:HAS_SUBCATEGORY]->(sub:Subcategory)
WITH cat, elementId(cat) as cat_elementId, cat.name as cat_name, cat.description as cat_description,
     CASE WHEN sub IS NOT NULL THEN {
         elementId: elementId(sub),
         name: sub.name,
         description: sub.description
     } ELSE NULL END as sub_data
ORDER BY sub.name
RETURN
    cat_elementId,
    cat_name,
    cat_description,
    collect(sub_data) as subcategories_data
LIMIT 1
"""

# Create a new top-level category
CREATE_CATEGORY = """
CREATE (c:Category {name: $name, description: $description})
RETURN elementId(c) as elementId, c.name as name, c.description as description
"""

# Check if a parent category exists
CHECK_PARENT_CATEGORY = """
MATCH (p:Category {name: $parent_name}) 
RETURN p LIMIT 1
"""

# Create a new subcategory under a parent category
CREATE_SUBCATEGORY = """
MATCH (p:Category {name: $parent_name})
CREATE (s:Subcategory {name: $sub_name, description: $sub_description})
MERGE (p)-[:HAS_SUBCATEGORY]->(s)
RETURN elementId(s) as elementId, s.name as name, s.description as description
"""

# Update a category (to be implemented)
UPDATE_CATEGORY = """
MATCH (c:Category {name: $name})
SET c.description = $description
RETURN elementId(c) as elementId, c.name as name, c.description as description
"""

# Update a subcategory (to be implemented)
UPDATE_SUBCATEGORY = """
MATCH (s:Subcategory {name: $name})
SET s.description = $description
RETURN elementId(s) as elementId, s.name as name, s.description as description
"""

# Delete a category (to be implemented)
DELETE_CATEGORY = """
MATCH (c:Category {name: $name})
DETACH DELETE c
"""

# Delete a subcategory (to be implemented)
DELETE_SUBCATEGORY = """
MATCH (s:Subcategory {name: $name})
DETACH DELETE s
"""

# Check if a category exists
CHECK_CATEGORY_EXISTS = """
MATCH (c:Category {name: $name})
RETURN count(c) > 0 AS exists
"""

# Check if a subcategory exists
CHECK_SUBCATEGORY_EXISTS = """
MATCH (s:Subcategory {name: $name})
RETURN count(s) > 0 AS exists
"""