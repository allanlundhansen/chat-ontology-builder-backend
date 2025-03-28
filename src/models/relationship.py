from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
import datetime

class RelationshipProperties(BaseModel):
    """Properties associated with a relationship."""
    # Common properties
    confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    creation_timestamp: Optional[datetime.datetime] = None # Often set by DB on creation

    # Spatial properties (optional)
    distance: Optional[float] = None
    spatial_unit: Optional[str] = None
    relation_type: Optional[str] = None # e.g., 'above', 'contains' for SPATIALLY_RELATES_TO

    # Temporal properties (optional)
    temporal_distance: Optional[float] = None
    temporal_unit: Optional[str] = None

    # Allow other arbitrary properties if needed, though explicit is better
    # model_config = ConfigDict(extra='allow')


class RelationshipCreate(BaseModel):
    """Schema for data required to create a new relationship."""
    type: str = Field(..., description="The type of the relationship (e.g., CAUSES, SPATIALLY_RELATES_TO)")
    source_id: str = Field(..., description="The element ID of the source concept node.")
    target_id: str = Field(..., description="The element ID of the target concept node.")
    properties: RelationshipProperties = Field(default_factory=RelationshipProperties, description="Properties for the relationship.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "CAUSES",
                    "source_id": "4:source-element-id:1",
                    "target_id": "4:target-element-id:2",
                    "properties": {"confidence": 0.9}
                },
                {
                    "type": "SPATIALLY_RELATES_TO",
                    "source_id": "4:source-element-id:3",
                    "target_id": "4:target-element-id:4",
                    "properties": {"distance": 10.5, "spatial_unit": "meters", "relation_type": "above", "confidence": 0.8}
                }
            ]
        }
    )

class RelationshipInfo(BaseModel):
    """Basic information about a relationship and connected nodes."""
    # Use NodeInfo or similar if you have a separate model for basic node details
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    rel_type: str = Field(..., alias="type") # Alias 'type' from DB to 'rel_type' if needed
    properties: Dict[str, Any]

    model_config = ConfigDict(
        populate_by_name=True, # Allow using alias 'type'
         json_schema_extra={
             "example": {
                 "source_id": "4:source-id:1",
                 "source_name": "Concept A",
                 "target_id": "4:target-id:2",
                 "target_name": "Concept B",
                 "rel_type": "CAUSES",
                 "properties": {"confidence": 0.9, "creation_timestamp": "2023-10-27T12:00:00Z"}
             }
         }
    )

class RelationshipResponse(RelationshipInfo):
    """Schema for the response when a relationship is created or retrieved."""
    # Inherits fields from RelationshipInfo
    # Can add specific fields if the creation query returns more/different info
    pass


# Specific info models used by endpoints in concepts.py (ensure these match query returns)
class TemporalRelationshipInfo(BaseModel):
    related_concept_id: str
    related_concept_name: str
    relationship_type: str # Should be 'PRECEDES'
    direction: str # 'incoming' or 'outgoing'
    properties: RelationshipProperties

class SpatialRelationshipInfo(BaseModel):
    related_concept_id: str
    related_concept_name: str
    relationship_type: str # Should be 'SPATIALLY_RELATES_TO'
    direction: str # 'incoming' or 'outgoing'
    properties: RelationshipProperties 