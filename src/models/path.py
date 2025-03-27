from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Re-using the Concept model is good, ensure it's accessible
# If path.py is separate, import it: from .concept import Concept
# If Concept is in concepts.py, this needs adjustment. Let's assume Concept is in models/concept.py
from src.models.concept import Concept # Adjust import if Concept model is elsewhere

class Relationship(BaseModel):
    """Represents a relationship within a path."""
    id: int # Internal Neo4j ID
    start_node_id: str # ID of the start Concept node
    end_node_id: str # ID of the end Concept node
    type: str # Type of the relationship (e.g., CAUSES)
    properties: Dict[str, Any] = {} # Relationship properties

class PathSegment(BaseModel):
    """Represents one segment (node, relationship, node) in a path."""
    start: Concept
    relationship: Relationship
    end: Concept

class PathResponse(BaseModel):
    """Represents a path returned from a query like getCausalChain."""
    nodes: List[Concept]
    relationships: List[Relationship]
    # Optional: segments representation if preferred
    # segments: List[PathSegment]

    # Helper function to convert Neo4j Path object
    @classmethod
    def from_neo4j_path(cls, path):
        nodes_map = {}
        rels_list = []

        for rel in path.relationships:
            start_node_data = dict(rel.start_node.items())
            end_node_data = dict(rel.end_node.items())

            # Ensure 'id' exists, fallback to element_id if needed (though our concepts should have 'id')
            start_node_id = start_node_data.get('id', rel.start_node.element_id)
            end_node_id = end_node_data.get('id', rel.end_node.element_id)

            # Add nodes to map, avoiding duplicates
            if start_node_id not in nodes_map:
                nodes_map[start_node_id] = Concept.model_validate(start_node_data)
            if end_node_id not in nodes_map:
                nodes_map[end_node_id] = Concept.model_validate(end_node_data)

            # Create relationship model
            rels_list.append(Relationship(
                id=rel.id, # Use internal ID for the relationship itself
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                type=rel.type,
                properties=dict(rel.items())
            ))

        return cls(nodes=list(nodes_map.values()), relationships=rels_list)
