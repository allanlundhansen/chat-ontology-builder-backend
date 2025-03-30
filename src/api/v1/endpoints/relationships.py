from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response
from neo4j import AsyncDriver, AsyncSession, AsyncTransaction, AsyncResult, Record, exceptions as neo4j_exceptions, ResultSummary
from pydantic import ValidationError
from typing import Optional, Dict, Any, List, Annotated
import traceback
import datetime

from src.db.neo4j_driver import get_db
from src.validation.kantian_validator import KantianValidator, KantianValidationError
# --- Import models from the correct location ---
from src.models.relationship import RelationshipCreate, RelationshipResponse, RelationshipProperties, RelationshipListResponse, RelationshipUpdate, RelationshipPropertiesUpdate

router = APIRouter()

@router.get(
    "/",
    response_model=RelationshipListResponse,
    summary="List Relationships",
    description="Retrieves a list of relationships, optionally filtered by type and paginated.",
    tags=["Relationships"]
)
async def handle_list_relationships(
    skip: int = Query(0, ge=0, description="Number of relationships to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of relationships to return"),
    type: Optional[str] = Query(None, description="Filter relationships by type (case-insensitive)"),
    session: AsyncSession = Depends(get_db)
):
    """Handles listing relationships with filtering and pagination."""
    try:
        # Build the Cypher query
        match_clause = "MATCH (source)-[rel]->(target)"
        where_clauses = []
        parameters = {}

        if type:
            # Use case-insensitive matching for type
            where_clauses.append("toUpper(type(rel)) = toUpper($rel_type)")
            parameters["rel_type"] = type

        where_clause = "" # Default to empty string
        if where_clauses:
            where_clause = " WHERE " + " AND ".join(where_clauses)

        # Query to get the relationships for the current page
        list_query = f"""
            {match_clause}
            {where_clause}
            RETURN
                elementId(rel) AS elementId,
                elementId(source) AS source_id,
                source.name AS source_name,
                elementId(target) AS target_id,
                target.name AS target_name,
                type(rel) AS type,
                properties(rel) AS properties
            ORDER BY properties(rel).creation_timestamp DESC
            SKIP $skip
            LIMIT $limit
        """
        parameters["skip"] = skip
        parameters["limit"] = limit

        # Query to get the total count (optional but good for pagination UI)
        count_query = f"""
            {match_clause}
            {where_clause}
            RETURN count(rel) AS total_count
        """
        # Remove pagination parameters for count query
        count_parameters = {k: v for k, v in parameters.items() if k not in ["skip", "limit"]}

        async def transaction_work(tx: AsyncTransaction, list_q: str, list_p: dict, count_q: str, count_p: dict):
            list_result: AsyncResult = await tx.run(list_q, list_p)
            # Fetch data as list of dictionaries
            records_data: List[Dict] = await list_result.data()
            relationships = [RelationshipResponse.model_validate(record_data) for record_data in records_data]

            count_result: AsyncResult = await tx.run(count_q, count_p)
            count_record: Optional[Record] = await count_result.single()
            total_count = count_record["total_count"] if count_record else 0

            return {"relationships": relationships, "total_count": total_count}

        result_data = await session.execute_read(
            lambda tx: transaction_work(tx, list_query, parameters, count_query, count_parameters)
        )

        return RelationshipListResponse.model_validate(result_data)

    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (List Relationships): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error listing relationships: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR (List Relationships): Pydantic validation failed: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing relationship data.")
    except Exception as e:
        print(f"ERROR (List Relationships): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while listing relationships.")

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
        # NOTE: Use apoc.nodes.get for potentially better transactional visibility
        # Try standard Cypher first
        # Define the transaction work function
        async def transaction_work(tx: AsyncTransaction, params: dict) -> dict:
            # Extract parameters for clarity
            source_id = params["source_id"]
            target_id = params["target_id"]
            rel_type = params["rel_type"]
            properties = params["properties"] # Raw properties from input

            # Add creation timestamp and filter out None values
            properties['creation_timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            final_properties = {k: v for k, v in properties.items() if v is not None}

            # Construct the query dynamically using f-string for relationship type
            query = f"""
            MATCH (source) WHERE elementId(source) = $source_id
            MATCH (target) WHERE elementId(target) = $target_id
            // Create the relationship with dynamic type
            CREATE (source)-[rel:`{rel_type}`]->(target)
            SET rel = $properties // Use filtered properties
            // Return data matching RelationshipResponse
            RETURN
                elementId(rel) AS elementId,
                elementId(source) AS source_id,
                source.name AS source_name,
                elementId(target) AS target_id,
                target.name AS target_name,
                type(rel) AS type,
                properties(rel) AS properties
            """

            # Prepare parameters for the transaction
            tx_params = {
                "source_id": source_id,
                "target_id": target_id,
                "properties": final_properties, # Pass the filtered properties
            }

            # Execute the query
            result = await tx.run(query, tx_params)
            record: Optional[Record] = await result.single() # Get the single record
            summary: ResultSummary = await result.consume() # Consume the result to get the summary

            if record is None:
                # print(f"DEBUG: Record is None. Nodes likely not found for IDs: {params.get('source_id')}, {params.get('target_id')}")
                raise ValueError(f"Could not create relationship. Source/Target node (elementId: {params.get('source_id')} or {params.get('target_id')}) might not exist.")

            # Now 'summary' is defined and can be used here
            if summary.counters.relationships_created != 1:
                # print(f"DEBUG: Relationships created count is {summary.counters.relationships_created}, expected 1.")
                # print(f"DEBUG: Full summary when creation failed: {summary.__dict__}")
                raise ValueError(f"Relationship creation failed unexpectedly after finding nodes (elementId: {params.get('source_id')}, {params.get('target_id')}). Summary: {summary}")

            # print(f"DEBUG: Transaction successful. Returning record data: {record.data()}")
            return record.data()

        created_rel_data = await session.execute_write(
            lambda tx: transaction_work(tx, {
                "source_id": rel_in.source_id,
                "target_id": rel_in.target_id,
                "rel_type": rel_in.type,
                "properties": rel_in.properties.model_dump(exclude_unset=False) # Pass raw properties dict
            })
        )

        if not created_rel_data:
            print(f"DEBUG: Record is None. Nodes likely not found for IDs: {rel_in.source_id}, {rel_in.target_id}")
            raise ValueError(f"Could not create relationship. Source/Target node (elementId: {rel_in.source_id} or {rel_in.target_id}) might not exist.")

        # Validate the DB data against the response model before returning
        return RelationshipResponse.model_validate(created_rel_data)

    except KantianValidationError as exc:
        raise exc # Handled by main.py exception handler
    except ValueError as val_err: # Catch node not found error
         print(f"ERROR (Create Relationship): Value error - {val_err}")
         # Reverted detail message
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

# Endpoint to get a specific relationship by its element ID
@router.get(
    "/{element_id}",
    response_model=RelationshipResponse,
    summary="Get Relationship by ID",
    description="Retrieve a single relationship by its unique element ID."
)
async def get_relationship_by_id(
    session: Annotated[AsyncSession, Depends(get_db)],
    element_id: str = Path(..., description="The unique element ID of the relationship to retrieve.")
) -> RelationshipResponse:
    """Retrieve a single relationship by its element ID."""
    query = (
        "MATCH (source)-[r]-(target) "
        "WHERE elementId(r) = $element_id "
        "RETURN "
        "    elementId(r) AS elementId, "
        "    type(r) AS type, "
        "    properties(r) AS properties, "
        "    elementId(source) AS source_id, "
        "    elementId(target) AS target_id "
    )

    try:
        result = await session.run(query, {"element_id": element_id})
        record = await result.single()
        
        if record is None:
            # Raise the 404, FastAPI will handle it correctly
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relationship with element ID '{element_id}' not found."
            )

        # Directly create the Pydantic model from the record dictionary
        return RelationshipResponse.model_validate(record.data())

    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Get Relationship by ID): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving relationship: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR (Get Relationship by ID): Pydantic validation failed: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing relationship data.")
    except Exception as e:
        print(f"ERROR (Get Relationship by ID): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving the relationship.")

# Endpoint to update a relationship by its element ID (PATCH)
@router.patch(
    "/{element_id}",
    response_model=RelationshipResponse,
    summary="Update Relationship Properties",
    description="Partially update the properties of a specific relationship by its unique element ID.",
    tags=["Relationships"]
)
async def update_relationship(
    update_data: RelationshipUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    element_id: str = Path(..., description="The unique element ID of the relationship to update.")
) -> RelationshipResponse:
    """Partially update a relationship's properties."""

    # Check if there's anything to update
    if not update_data.properties:
        # Optionally, return the existing relationship without modification or raise 400
        # For now, let's just fetch and return the current state if no update data provided
        return await get_relationship_by_id(session=session, element_id=element_id)

    # Use model_dump to get only explicitly set fields in the request payload
    update_payload = update_data.properties.model_dump(exclude_unset=True)

    if not update_payload:
        # If properties object was provided but empty
        return await get_relationship_by_id(session=session, element_id=element_id)

    # Perform Kantian Validation on the properties being updated
    # Need the relationship type first
    fetch_type_query = "MATCH ()-[r]-() WHERE elementId(r) = $element_id RETURN type(r) as type"
    try:
        type_result = await session.run(fetch_type_query, {"element_id": element_id})
        type_record = await type_result.single()
        if not type_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Relationship with element ID '{element_id}' not found.")
        rel_type = type_record["type"]

        # Validate the update payload against the type
        KantianValidator.validate_relationship(rel_type, update_payload)

    except KantianValidationError as exc:
        raise exc # Let main handler manage this
    except HTTPException as http_exc: # Add this block to handle specific HTTP exceptions first
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Update Relationship - Precheck): Database error fetching type - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during pre-update check: {db_err.code}")
    except Exception as e:
         print(f"ERROR (Update Relationship - Precheck): Unexpected error - {e}")
         traceback.print_exc()
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during pre-update check.")

    # Build the SET clause dynamically if needed, or just use += for properties
    # Using += is simpler if we only update properties
    query = (
        "MATCH (source)-[r]-(target) "
        "WHERE elementId(r) = $element_id "
        "SET r += $update_payload " # Merges the new properties into the existing ones
        "RETURN "
        "    elementId(r) AS elementId, "
        "    type(r) AS type, "
        "    properties(r) AS properties, "
        "    elementId(source) AS source_id, "
        "    elementId(target) AS target_id "
    )

    try:
        result = await session.run(query, {"element_id": element_id, "update_payload": update_payload})
        record = await result.single()
        summary = await result.consume()

        # Check if the relationship was found and updated
        if record is None or summary.counters.properties_set == 0:
            # If the relationship didn't exist, the MATCH would fail, record is None
            # If SET didn't do anything (unlikely with +=), properties_set might be 0
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relationship with element ID '{element_id}' not found or no properties updated."
            )

        # Validate and return the updated relationship
        return RelationshipResponse.model_validate(record.data())

    except HTTPException as http_exc: # Re-raise HTTPExceptions (like 404 or validation error)
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Update Relationship): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error updating relationship: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR (Update Relationship): Pydantic validation failed for updated data: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing updated relationship.")
    except Exception as e:
        print(f"ERROR (Update Relationship): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the relationship.")

# Endpoint to delete a relationship by its element ID
@router.delete(
    "/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Relationship by ID",
    description="Delete a specific relationship by its unique element ID.",
    tags=["Relationships"]
)
async def delete_relationship(
    session: Annotated[AsyncSession, Depends(get_db)],
    element_id: str = Path(..., description="The unique element ID of the relationship to delete.")
):
    """Delete a relationship by its unique element ID."""
    query = (
        "MATCH ()-[r]-() "
        "WHERE elementId(r) = $element_id "
        "DETACH DELETE r "
        "RETURN count(r) as deleted_count"
    )
    try:
        result = await session.run(query, {"element_id": element_id})
        summary = await result.consume()

        # Check if any relationship was actually deleted
        # Neo4j counts relationships deleted in the summary
        if summary.counters.relationships_deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relationship with element ID '{element_id}' not found."
            )
        
        # If deletion was successful, return 204 No Content
        # FastAPI handles this automatically based on the status_code in the decorator
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException as http_exc: # Re-raise 404
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Delete Relationship): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error deleting relationship: {db_err.code}")
    except Exception as e:
        print(f"ERROR (Delete Relationship): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while deleting the relationship.") 