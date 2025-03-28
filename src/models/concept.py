from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class Concept(BaseModel):
    """Represents a concept node retrieved from the database."""
    id: str
    name: str
    description: Optional[str] = None
    # Use alias to map from 'confidence_score' in DB to 'confidence' in model
    confidence: Optional[float] = Field(None, alias='confidence_score')

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
                "name": "Example Concept",
                "description": "A brief description of the concept.",
                "confidence": 0.95
            }
        }
    ) 