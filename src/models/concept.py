from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import datetime # Import datetime

class Concept(BaseModel):
    """Represents a concept node retrieved from the database."""
    id: str # Usually the Neo4j internal ID or a custom UUID
    elementId: Optional[str] = None # Neo4j internal element ID
    name: str
    description: Optional[str] = None
    quality: Optional[str] = None
    modality: Optional[str] = None
    stability: Optional[str] = None
    # Use alias to map from 'confidence_score' in DB to 'confidence' in model
    confidence_score: Optional[float] = Field(None, alias='confidence')
    created_at: Optional[datetime.datetime] = None # Add timestamp field

    # Updated configuration using ConfigDict
    model_config = ConfigDict(
        # Allow Pydantic to populate the model even if the input key
        # is 'confidence_score' instead of 'confidence'.
        # Note: Field(alias=...) often handles this, but populate_by_name is still valid in V2
        populate_by_name=True,
        # Add an example for the OpenAPI documentation
        json_schema_extra={
            "example": {
                "id": "uuid-of-concept",
                "elementId": "4:element-id-string:123",
                "name": "Example Concept",
                "description": "A brief description of the concept.",
                "quality": "Reality",
                "modality": None,
                "stability": "stable",
                "confidence": 0.95,
                "created_at": "2023-10-27T10:00:00Z"
            }
        }
    )

class ConceptCreate(BaseModel):
    """Schema for data required to create a new concept."""
    name: str = Field(..., min_length=1, description="The primary name of the concept.")
    description: Optional[str] = Field(None, description="A textual description of the concept.")
    quality: Optional[str] = Field(None, description="Kantian Quality (Reality/Negation/Limitation).")
    # Mark modality as deprecated for creation input if desired
    modality: Optional[str] = Field(None, description="Kantian Modality (Possibility/Impossibility, Existence/Non-existence, Necessity/Contingency) - DEPRECATED in Phase 1 input.")
    stability: Optional[str] = Field('ephemeral', description="Stability status (e.g., 'ephemeral', 'stable').")
    confidence: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Confidence score associated with the concept.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "New Concept Example",
                    "description": "Details about this new concept.",
                    "quality": "Reality",
                    "stability": "ephemeral",
                    "confidence": 0.75
                }
            ]
        }
    )

# Often similar to the main Concept model, but can be tailored
class ConceptResponse(Concept):
    """Schema for the response when a concept is created or retrieved."""
    # Inherits all fields from Concept
    # You can add or override fields specifically for responses if needed
    pass

# Properties that can be received PATCH requests for a concept
class ConceptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    quality: Optional[str] = None
    modality: Optional[str] = None
    stability: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0) # Keep validation if present in Base 