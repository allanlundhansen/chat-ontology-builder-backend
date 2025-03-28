from src.models.relationship import RelationshipCreate  # Now using model from existing structure
from src.validators.kantian_validator import KantianValidator
from fastapi import HTTPException

class RelationshipService:
    def create_relationship(self, rel_data: dict) -> dict:
        try:
            # First validate through Pydantic model
            relationship = RelationshipCreate.model_validate(rel_data)
            
            # Then apply Kantian validation rules
            KantianValidator.validate_relationship(
                relationship.type,
                relationship.properties
            )
            
        except ValidationError as e:
            raise HTTPException(422, detail=e.errors())
        except KantianValidationError as e:
            raise HTTPException(422, detail={
                "msg": str(e),
                "type": "kantian_validation",
                "field": e.field
            })

        # Rest of the service logic remains the same 