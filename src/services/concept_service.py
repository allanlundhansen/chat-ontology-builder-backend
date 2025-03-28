from typing import Optional
from pydantic import BaseModel, Field
from ..validation.kantian_validator import KantianValidator, KantianValidationError

class ConceptCreate(BaseModel):
    name: str
    quality: Optional[str] = Field(
        None, 
        description="Phase 1 Quality category (Reality/Negation/Limitation)"
    )
    modality: Optional[str] = Field(
        None,
        description="DEPRECATED: Will transition to judgment relationships in Phase 2"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "name": "CausalForce",
                "quality": "Reality",
                "modality": "Necessity/Contingency"
            }
        }

class ConceptService:
    def __init__(self, db_session):
        self.db = db_session
    
    def create_concept(self, concept_data: dict) -> dict:
        # Validate before processing
        try:
            KantianValidator.validate_concept(concept_data)
        except KantianValidationError as e:
            self._log_validation_error(e)
            raise
        
        # Proceed with database operations
        query = """
        CREATE (c:Concept $params)
        RETURN c
        """
        return self.db.execute(query, {"params": concept_data})
    
    def _log_validation_error(self, error: KantianValidationError):
        # Implement logging integration here
        pass 