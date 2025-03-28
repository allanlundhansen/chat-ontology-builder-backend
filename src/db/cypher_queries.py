QUERIES = {
    "getConceptProperties": """
        MATCH (c:Concept {id: $conceptId})-[:HAS_PROPERTY]->(prop:Concept)
        RETURN prop
    """,
    "getInteractingConcepts": """
        MATCH (c:Concept {id: $conceptId})-[:INTERACTS_WITH]->(related:Concept)
        RETURN related
    """,
} 