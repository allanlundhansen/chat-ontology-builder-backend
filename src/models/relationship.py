from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
import datetime

class RelationshipProperties(BaseModel):
    """Properties associated with a relationship."""
    # Common properties
    confidence_score: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    created_at: Optional[datetime.datetime] = None # Renamed from creation_timestamp
    updated_at: Optional[datetime.datetime] = None # Added updated_at
    source_information: Optional[str] = None # Added source information

    # Spatial properties (optional)
    distance: Optional[float] = None
    spatial_unit: Optional[str] = None
    relation_type: Optional[str] = None # e.g., 'above', 'contains' for SPATIALLY_RELATES_TO
    spatial_dimension: Optional[str] = None # ADDED FIELD

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
                    "properties": {"confidence_score": 0.9}
                },
                {
                    "type": "SPATIALLY_RELATES_TO",
                    "source_id": "4:source-element-id:3",
                    "target_id": "4:target-element-id:4",
                    "properties": {"distance": 10.5, "spatial_unit": "meters", "relation_type": "above", "confidence_score": 0.8}
                }
            ]
        }
    )

class RelationshipInfo(BaseModel):
    """Basic information about a relationship and connected nodes."""
    # Use NodeInfo or similar if you have a separate model for basic node details
    source_id: str
    source_name: Optional[str] = None # Made optional
    target_id: str
    target_name: Optional[str] = None # Made optional
    rel_type: str = Field(..., alias="type") # Alias 'type' from DB to 'rel_type' if needed
    properties: RelationshipProperties

    model_config = ConfigDict(
        populate_by_name=True, # Allow using alias 'type'
         json_schema_extra={
             "example": {
                 "source_id": "4:source-id:1",
                 "source_name": "Concept A",
                 "target_id": "4:target-id:2",
                 "target_name": "Concept B",
                 "rel_type": "CAUSES",
                 "properties": {"confidence_score": 0.9, "created_at": "2023-10-27T12:00:00Z"}
             }
         }
    )

class RelationshipResponse(RelationshipInfo):
    """Schema for the response when a relationship is created or retrieved."""
    # Inherits fields from RelationshipInfo
    elementId: str # Changed from element_id to elementId
    # Can add specific fields if the creation query returns more/different info
    pass


# Specific info models used by endpoints in concepts.py (ensure these match query returns)
class TemporalRelationshipInfo(BaseModel):
    elementId: str
    related_concept_id: str
    related_concept_name: str
    relationship_type: str # Should be 'PRECEDES'
    direction: str # 'incoming' or 'outgoing'
    properties: RelationshipProperties

class SpatialRelationshipInfo(BaseModel):
    elementId: str
    related_concept_id: str
    related_concept_name: str
    relationship_type: str # Should be 'SPATIALLY_RELATES_TO'
    direction: str # 'incoming' or 'outgoing'
    properties: RelationshipProperties

class RelationshipListResponse(BaseModel):
    """Schema for the response when listing relationships."""
    relationships: List[RelationshipResponse]
    total_count: Optional[int] = None # Optional: Include total count for pagination

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "relationships": [
                    {
                        "element_id": "5:rel-element-id:123", # Added element_id
                        "source_id": "4:source-id:1",
                        "source_name": "Concept A",
                        "target_id": "4:target-id:2",
                        "target_name": "Concept B",
                        "rel_type": "CAUSES",
                        "properties": {"confidence_score": 0.9, "created_at": "2023-10-27T12:00:00Z"}
                    },
                    {
                        "element_id": "5:rel-element-id:456", # Added element_id
                        "source_id": "4:source-id:3",
                        "source_name": "Concept C",
                        "target_id": "4:target-id:4",
                        "rel_type": "IS_PART_OF",
                        "properties": {"confidence_score": 1.0, "created_at": "2023-10-28T10:00:00Z"}
                    }
                ],
                "total_count": 42 # Example total count
            }
        }
    )


class RelationshipPropertiesUpdate(BaseModel):
    """Properties that can be updated on a relationship. All fields are optional."""
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    # created_at is generally system-set, probably shouldn't be updatable by user PATCH
    updated_at: Optional[datetime.datetime] = None # Added updated_at
    source_information: Optional[str] = None # Added source information
    distance: Optional[float] = None
    spatial_unit: Optional[str] = None
    relation_type: Optional[str] = None
    spatial_dimension: Optional[str] = None # ADDED FIELD
    temporal_distance: Optional[float] = None
    temporal_unit: Optional[str] = None

    # Prevent extra fields during update?
    model_config = ConfigDict(extra='forbid')

class RelationshipUpdate(BaseModel):
    """Schema for data allowed when updating a relationship via PATCH."""
    # Only properties are updatable via PATCH in this design
    properties: Optional[RelationshipPropertiesUpdate] = Field(None, description="Optional new properties for the relationship. Only provided fields will be updated.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "properties": {"confidence_score": 0.95}
                },
                {
                    "properties": {"distance": 12.0, "spatial_unit": "km"}
                }
            ]
        }
    ) 