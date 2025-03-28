from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class RelationshipInfo(BaseModel):
    """Represents basic information about a relationship and the connected concept."""
    relationship_type: str = Field(..., description="The type of the relationship (e.g., 'CAUSES', 'HAS_PROPERTY').")
    other_id: str = Field(..., alias='otherId', description="The unique ID of the concept on the other end of the relationship.")
    other_name: str = Field(..., alias='otherName', description="The name of the concept on the other end.")
    confidence: Optional[float] = Field(None, description="Confidence score associated with the relationship.")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "relationship_type": "CAUSES",
                "other_id": "uuid-of-effect-concept",
                "other_name": "Effect Concept Name",
                "confidence": 0.85
            }
        }
    )

class TemporalRelationshipInfo(BaseModel):
    """Represents information about a temporal relationship (PRECEDES)."""
    id: str = Field(..., description="The unique ID of the related concept (before or after).")
    name: str = Field(..., description="The name of the related concept.")
    description: Optional[str] = None
    temporal_distance: Optional[str] = Field(None, alias='temporalDistance', description="Description of the time between concepts (e.g., 'seconds', 'immediately').")
    confidence: Optional[float] = Field(None, description="Confidence score associated with the relationship.")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "uuid-of-thunder",
                "name": "Thunder",
                "description": "Sound caused by lightning.",
                "temporal_distance": "seconds",
                "confidence": 0.99
            }
        }
    )

class SpatialRelationshipInfo(BaseModel):
    """Represents information about a spatial relationship (SPATIALLY_RELATES_TO)."""
    id: str = Field(..., description="The unique ID of the related concept.")
    name: str = Field(..., description="The name of the related concept.")
    description: Optional[str] = None
    relation_type: Optional[str] = Field(None, alias='relationType', description="Type of spatial relationship (e.g., 'contains', 'adjacent', 'orbits').")
    distance: Optional[str] = Field(None, description="Description of the distance between concepts.")
    confidence: Optional[float] = Field(None, description="Confidence score associated with the relationship.")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "uuid-of-moon",
                "name": "Moon",
                "description": "Natural satellite of Earth.",
                "relation_type": "orbits",
                "distance": "384400 km",
                "confidence": 1.0
            }
        }
    ) 