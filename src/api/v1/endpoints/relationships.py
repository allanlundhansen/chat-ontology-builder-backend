from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import AsyncSession, AsyncTransaction, AsyncResult, Record, exceptions as neo4j_exceptions
from pydantic import ValidationError
from typing import Optional, Dict, Any
import traceback

from src.db.neo4j_driver import get_db
from src.validation.kantian_validator import KantianValidator, KantianValidationError
# --- Import models from the correct location ---
from src.models.relationship import RelationshipCreate, RelationshipResponse, RelationshipProperties

router = APIRouter()

@router.post(
    "/",
    response_model=RelationshipResponse, # Use imported response model
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Relationship",
    description="Creates a new relationship between two existing concepts after validation.",
    tags=["Relationships"]
)
async def handle_create_relationship(
    rel_in: RelationshipCreate, # Use imported input model
    session: AsyncSession = Depends(get_db)
):
    """Handles the creation of a new relationship."""
    try:
        # 1. Perform Kantian Validation (Pydantic checks done)
        # Pass properties dict to validator
        # Use exclude_unset=True to only pass properties explicitly provided in the request
        props_to_validate = rel_in.properties.model_dump(exclude_unset=True)
        KantianValidator.validate_relationship(rel_in.type, props_to_validate)

        # 2. Database Interaction
        # NOTE: Ensure this Cypher query is correct for your setup and handles dynamic types/properties safely.
        create_rel_query = """
            MATCH (source) WHERE elementId(source) = $source_id
            MATCH (target) WHERE elementId(target) = $target_id
            CALL apoc.create.relationship(source, $rel_type, $properties, target) YIELD rel
            // Set timestamp AFTER relationship creation
            SET rel.creation_timestamp = datetime()
            // Return data matching RelationshipResponse (aliased from RelationshipInfo)
            RETURN
                elementId(source) AS source_id,
                source.name AS source_name,
                elementId(target) AS target_id,
                target.name AS target_name,
                type(rel) AS type, // Alias required if RelationshipInfo uses 'rel_type'
                properties(rel) AS properties
        """
        # Prepare parameters
        # Get properties from the Pydantic model, ensuring defaults are included but exclude unset optional ones
        # This passes only what the user sent plus defaults, preventing sending None for unset optional fields
        final_properties = rel_in.properties.model_dump(exclude_unset=False) # Include defaults
        # Remove None values explicitly if apoc.create.relationship has issues with them
        # final_properties = {k: v for k, v in final_properties.items() if v is not None}


        parameters = {
            "source_id": rel_in.source_id,
            "target_id": rel_in.target_id,
            "rel_type": rel_in.type.upper(),
            "properties": final_properties # Pass the prepared properties
        }

        async def transaction_work(tx: AsyncTransaction, query: str, params: dict):
            result: AsyncResult = await tx.run(query, params)
            record: Optional[Record] = await result.single()
            summary = await result.consume()
            if record is None or summary.relationships_created != 1:
                 raise ValueError(f"Could not create relationship. Source/Target node (elementId: {params.get('source_id')} or {params.get('target_id')}) might not exist, or another issue occurred.")
            return record.data()

        created_rel_data = await session.execute_write(
            lambda tx: transaction_work(tx, create_rel_query, parameters)
        )

        # Validate the DB data against the response model before returning
        return RelationshipResponse.model_validate(created_rel_data)

    except KantianValidationError as exc:
        raise exc # Handled by main.py exception handler
    except ValueError as val_err: # Catch node not found error
         print(f"ERROR (Create Relationship): Value error - {val_err}")
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Create Relationship): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {db_err.code}")
    except ValidationError as pydantic_err: # Error validating DB result
         print(f"ERROR (Create Relationship): Pydantic validation failed for DB result: {pydantic_err}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing created relationship.")
    except Exception as e:
        print(f"ERROR (Create Relationship): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.") 