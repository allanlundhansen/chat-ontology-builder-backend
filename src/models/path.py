from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

# Re-using the Concept model is good, ensure it's accessible
# If path.py is separate, import it: from .concept import Concept
# If Concept is in concepts.py, this needs adjustment. Let's assume Concept is in models/concept.py
from src.models.concept import Concept # Adjust import if Concept model is elsewhere

# Import the converter from the NEW location
from src.utils.converters import convert_neo4j_datetimes

class Relationship(BaseModel):
    """Represents a relationship within a path."""
    # Made id optional as it's not directly available in the list format
    id: Optional[int] = None # Internal Neo4j ID is not easily accessible here
    start_node_id: str # Use elementId
    end_node_id: str # Use elementId
    type: str # Type of the relationship (e.g., CAUSES)
    properties: Dict[str, Any] = {} # Relationship properties (likely empty from path list)

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

    # Helper function to convert Neo4j Path representation from result.data()
    @classmethod
    def from_neo4j_path(cls, path_data: List[Union[Dict, str]]):
        """
        Parses the list representation of a Neo4j path returned by
        AsyncResult.data() when the query returns a path directly (e.g., RETURN path).
        Example input: [{node1_dict}, 'REL_TYPE', {node2_dict}, ...]
        """
        nodes_map = {}
        rels_list = []

        if not path_data or not isinstance(path_data, list):
            return cls(nodes=[], relationships=[]) # Return empty if input is invalid

        # 1. Extract and process all nodes
        for i in range(0, len(path_data), 2): # Nodes are at even indices
            if i < len(path_data) and isinstance(path_data[i], dict):
                node_dict = path_data[i]
                # --- Convert datetimes before validation ---
                native_node_dict = convert_neo4j_datetimes(node_dict)
                # --- Get elementId ---
                # Use 'elementId' if present, otherwise fallback (though it should be there from our queries)
                node_element_id = native_node_dict.get('elementId')
                if node_element_id and node_element_id not in nodes_map:
                    try:
                        nodes_map[node_element_id] = Concept.model_validate(native_node_dict)
                    except Exception as e:
                        print(f"WARN: Failed to validate node data in path: {native_node_dict}. Error: {e}")
                        # Decide how to handle invalid nodes in path, maybe skip?

        # 2. Extract and process all relationships
        for i in range(0, len(path_data) - 2, 2): # Iterate through segments: node, rel_type, node
            start_node_dict = path_data[i]
            rel_type = path_data[i+1]
            end_node_dict = path_data[i+2]

            if isinstance(start_node_dict, dict) and isinstance(rel_type, str) and isinstance(end_node_dict, dict):
                start_node_id = convert_neo4j_datetimes(start_node_dict).get('elementId')
                end_node_id = convert_neo4j_datetimes(end_node_dict).get('elementId')

                if start_node_id and end_node_id:
                    # Create relationship model (id and properties are mostly unavailable here)
                    rels_list.append(Relationship(
                        start_node_id=start_node_id,
                        end_node_id=end_node_id,
                        type=rel_type,
                        # properties={} # Properties are not in the list structure
                    ))
                else:
                     print(f"WARN: Could not find elementId for start or end node in path segment: Start={start_node_dict}, End={end_node_dict}")
            else:
                 print(f"WARN: Unexpected structure in path segment at index {i}: {path_data[i:i+3]}")


        return cls(nodes=list(nodes_map.values()), relationships=rels_list)
