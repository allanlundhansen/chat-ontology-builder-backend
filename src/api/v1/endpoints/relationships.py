from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Response
from neo4j import AsyncDriver, AsyncTransaction, AsyncResult, Record, exceptions as neo4j_exceptions, ResultSummary
from pydantic import ValidationError
from typing import Optional, Dict, Any, List, Annotated
import traceback
import datetime

from src.db.neo4j_driver import get_db
from src.validation.kantian_validator import KantianValidator, KantianValidationError
# --- Import models from the correct location ---
from src.models.relationship import RelationshipCreate, RelationshipResponse, RelationshipProperties, RelationshipListResponse, RelationshipUpdate, RelationshipPropertiesUpdate
# --- Import the datetime conversion helper --- #
from src.api.v1.endpoints.concepts import convert_neo4j_datetimes

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
    tx: AsyncTransaction = Depends(get_db)
):
    """Handles listing relationships with filtering and pagination."""
    endpoint_name = "ListRelationships"
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
            ORDER BY properties(rel).created_at DESC
            SKIP $skip
            LIMIT $limit
        """
        list_parameters = {**parameters, "skip": skip, "limit": limit}

        # Query to get the total count (optional but good for pagination UI)
        count_query = f"""
            {match_clause}
            {where_clause}
            RETURN count(rel) AS total_count
        """
        count_parameters = parameters # Use the same base parameters

        # Execute list query directly using tx.run()
        print(f"DEBUG ({endpoint_name}): Executing list query: {list_query} with params: {list_parameters}")
        list_result: AsyncResult = await tx.run(list_query, list_parameters)
        records_data: List[Dict] = await list_result.data() # Fetch data as list of dictionaries
        list_summary = await list_result.consume()
        print(f"DEBUG ({endpoint_name}): List query executed. Summary: {list_summary.counters}. Found {len(records_data)} records.")

        # Validate relationships, converting datetimes within properties first
        relationships = []
        for record_data in records_data:
            if 'properties' in record_data and record_data['properties']:
                # Convert datetimes within the properties dict
                record_data['properties'] = convert_neo4j_datetimes(record_data['properties'])
            try:
                relationships.append(RelationshipResponse.model_validate(record_data))
            except ValidationError as val_err:
                print(f"ERROR ({endpoint_name}): Pydantic validation failed for record: {record_data}. Error: {val_err}")
                # Optionally skip or raise, here we skip and log

        # Execute count query directly using tx.run()
        print(f"DEBUG ({endpoint_name}): Executing count query: {count_query} with params: {count_parameters}")
        count_result: AsyncResult = await tx.run(count_query, count_parameters)
        count_record: Optional[Record] = await count_result.single()
        count_summary = await count_result.consume()
        print(f"DEBUG ({endpoint_name}): Count query executed. Summary: {count_summary.counters}.")
        total_count = count_record["total_count"] if count_record else 0

        # Construct response
        result_data = {"relationships": relationships, "total_count": total_count}

        return RelationshipListResponse.model_validate(result_data)

    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error listing relationships: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR ({endpoint_name}): Pydantic validation failed: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing relationship data.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
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
    tx: AsyncTransaction = Depends(get_db)
):
    """Handles the creation of a new relationship."""
    endpoint_name = "CreateRelationship"
    try:
        # 1. Perform Kantian Validation (Pydantic checks done)
        # Pass properties dict to validator
        # Use exclude_unset=True to only pass properties explicitly provided in the request
        props_to_validate = rel_in.properties.model_dump(exclude_unset=True)
        KantianValidator.validate_relationship(rel_in.type, props_to_validate)
        print(f"DEBUG ({endpoint_name}): Kantian validation passed for type {rel_in.type}.")

        # 2. Prepare parameters and query
        source_id = rel_in.source_id
        target_id = rel_in.target_id
        rel_type = rel_in.type
        # Start with input properties, add timestamp, filter None
        properties = rel_in.properties.model_dump(exclude_unset=False) # Get all, including defaults
        properties["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        properties["updated_at"] = properties["created_at"] # Set updated_at on creation
        final_properties = {k: v for k, v in properties.items() if v is not None}

        # Construct the query dynamically
        query = f"""
        MATCH (source) WHERE elementId(source) = $source_id
        MATCH (target) WHERE elementId(target) = $target_id
        CREATE (source)-[rel:`{rel_type}`]->(target)
        SET rel = $properties // Use filtered properties
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

        # 3. Execute Write Transaction directly using tx.run()
        print(f"DEBUG ({endpoint_name}): Executing query: {query} with params: {tx_params}")
        result: AsyncResult = await tx.run(query, tx_params)
        record: Optional[Record] = await result.single() # Get the single record
        summary: ResultSummary = await result.consume() # Consume the result
        print(f"DEBUG ({endpoint_name}): Query executed. Summary: {summary.counters}")

        # Check if the relationship was created and data returned
        if record and summary.counters.relationships_created == 1:
            created_rel_data = record.data()
            print(f"DEBUG ({endpoint_name}): Relationship created successfully: {created_rel_data}")
            # Validate the DB data against the response model
            return RelationshipResponse.model_validate(created_rel_data)
        elif record is None and summary.counters.relationships_created == 0:
            # Check if nodes were found before concluding it's a 404
            # Run checks within the same transaction for consistency
            source_exists_res = await tx.run("MATCH (n) WHERE elementId(n) = $id RETURN count(n) > 0 AS exists", {"id": source_id})
            source_exists = (await source_exists_res.single())['exists']
            await source_exists_res.consume()
            target_exists_res = await tx.run("MATCH (n) WHERE elementId(n) = $id RETURN count(n) > 0 AS exists", {"id": target_id})
            target_exists = (await target_exists_res.single())['exists']
            await target_exists_res.consume()

            if not source_exists or not target_exists:
                missing_id = source_id if not source_exists else target_id
                error_detail = f"Could not create relationship. Source/Target node (elementId: {missing_id}) not found."
                print(f"INFO ({endpoint_name}): {error_detail}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
            else:
                # Nodes exist but relationship wasn't created - unexpected DB issue?
                error_detail = f"Relationship creation failed unexpectedly after finding nodes. Summary: {summary}"
                print(f"ERROR ({endpoint_name}): {error_detail}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error during relationship creation.")
        else:
            # Other unexpected cases
            error_detail = f"Relationship creation failed. Record: {record.data() if record else 'None'}, Summary: {summary}"
            print(f"ERROR ({endpoint_name}): {error_detail}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error creating relationship.")

    except KantianValidationError as exc:
        print(f"ERROR ({endpoint_name}): Kantian validation failed - {exc}")
        # Let the main handler manage the 422 response
        raise exc
    except HTTPException as http_err: # Re-raise 404 or other HTTP exceptions
        raise http_err
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {db_err.code}")
    except ValidationError as pydantic_err: # Error validating DB result
        print(f"ERROR ({endpoint_name}): Pydantic validation failed for DB result: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing created relationship.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
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
    tx: Annotated[AsyncTransaction, Depends(get_db)],
    element_id: str = Path(..., description="The unique element ID of the relationship to retrieve.")
) -> RelationshipResponse:
    """Retrieve a single relationship by its element ID."""
    endpoint_name = f"GetRelationshipByID:{element_id}"
    query = (
        "MATCH (source)-[r]-(target) "
        "WHERE elementId(r) = $element_id "
        "RETURN "
        "    elementId(r) AS elementId, "
        "    type(r) AS type, "
        "    properties(r) AS properties, "
        "    elementId(source) AS source_id, "
        "    source.name AS source_name, "
        "    elementId(target) AS target_id, "
        "    target.name AS target_name "
    )
    params = {"element_id": element_id}

    print(f"DEBUG ({endpoint_name}): Executing query: {query} with params: {params}")

    try:
        # Use tx.run() directly
        result: AsyncResult = await tx.run(query, params)
        record: Optional[Record] = await result.single()
        summary = await result.consume()
        print(f"DEBUG ({endpoint_name}): Query executed. Summary: {summary.counters}")

        if record is None:
            # Raise the 404
            detail = f"Relationship with element ID '{element_id}' not found."
            print(f"INFO ({endpoint_name}): {detail}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail
            )

        # Validate the returned data
        rel_data = record.data()
        print(f"DEBUG ({endpoint_name}): Relationship found: {rel_data}")
        return RelationshipResponse.model_validate(rel_data)

    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        raise http_exc
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving relationship: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR ({endpoint_name}): Pydantic validation failed for DB result: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing relationship data.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred retrieving the relationship.")

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
    element_id: str = Path(..., description="The unique element ID of the relationship to update."),
    tx: AsyncTransaction = Depends(get_db)
) -> RelationshipResponse:
    """Partially update a relationship's properties."""
    endpoint_name = f"UpdateRelationship:{element_id}"

    # Check if properties are provided and not None
    if update_data.properties is None:
        update_payload = {} # No properties to update
    else:
        # Get properties to update, excluding None values
        update_payload = update_data.properties.model_dump(exclude_unset=True)

    # Prevent updating with an empty properties dictionary if that's the intent
    # Or handle fetching and returning existing if payload is empty

    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No properties provided for update."
        )

    # Add updated_at timestamp
    update_payload["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Validate the *updated* properties against Kantian rules
    # We need the relationship type for context. We can get it in the same transaction.

    # Build SET clauses dynamically
    set_clauses = []
    for key, value in update_payload.items():
        set_clauses.append(f"r.{key} = ${key}")
    set_statement = ", ".join(set_clauses)

    # Combined query to get type, validate, update, and return
    query = f"""
    MATCH (source)-[r]-(target)
    WHERE elementId(r) = $element_id
    WITH r, source, target, type(r) as current_type
    // Apply the SET clause
    SET {set_statement}
    // Return the updated relationship details
    RETURN
        elementId(r) AS elementId,
        elementId(source) AS source_id,
        source.name AS source_name,
        elementId(target) AS target_id,
        target.name AS target_name,
        type(r) AS type, // Return the type
        properties(r) AS properties // Return updated properties
    """

    params = {"element_id": element_id, **update_payload} # Combine ID and update data

    print(f"DEBUG ({endpoint_name}): Executing update query: {query} with params: {params}")

    try:
        # Run the combined query
        result: AsyncResult = await tx.run(query, params)
        record: Optional[Record] = await result.single()
        summary = await result.consume()
        print(f"DEBUG ({endpoint_name}): Update query executed. Summary: {summary.counters}")

        if record and summary.counters.properties_set > 0:
            updated_rel_data = record.data()
            # --- Convert datetimes before validation --- #
            if 'properties' in updated_rel_data and updated_rel_data['properties']:
                converted_properties = convert_neo4j_datetimes(updated_rel_data['properties'])
                updated_rel_data['properties'] = converted_properties # Update the dict for model validation
            else:
                converted_properties = {}

            # Perform Kantian validation *after* getting the type and updated props
            try:
                KantianValidator.validate_relationship(updated_rel_data['type'], converted_properties)
                print(f"DEBUG ({endpoint_name}): Kantian validation passed for updated properties.")
            except KantianValidationError as val_err:
                # If validation fails *after* update, this is tricky. Ideally, validate before SET.
                # For now, raise 422, though DB state is already changed.
                # Consider a two-step transaction or pre-flight check if strict atomicity is needed.
                print(f"ERROR ({endpoint_name}): Kantian validation failed AFTER update: {val_err}")
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err))

            print(f"DEBUG ({endpoint_name}): Relationship updated successfully: {updated_rel_data}")
            # Now validate the full response data (with converted properties)
            return RelationshipResponse.model_validate(updated_rel_data)

        elif record is None and summary.counters.properties_set == 0:
            # Relationship not found
            detail = f"Relationship with element ID '{element_id}' not found for update."
            print(f"INFO ({endpoint_name}): {detail}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        else:
            # Relationship found but no properties set? Unexpected.
            error_detail = f"Update failed unexpectedly. Record: {record.data() if record else 'None'}, Summary: {summary}"
            print(f"ERROR ({endpoint_name}): {error_detail}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during relationship update.")

    except KantianValidationError as exc: # If validation before query fails (if implemented)
        print(f"ERROR ({endpoint_name}): Kantian validation failed - {exc}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException as http_exc: # Re-raise 404, 400, 422
        raise http_exc
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error updating relationship: {db_err.code}")
    except ValidationError as pydantic_err: # Error validating DB result
        print(f"ERROR ({endpoint_name}): Pydantic validation failed for updated DB result: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing updated relationship data.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred updating the relationship.")

# Endpoint to delete a relationship by its element ID
@router.delete(
    "/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Relationship by ID",
    description="Delete a specific relationship by its unique element ID.",
    tags=["Relationships"]
)
async def delete_relationship(
    element_id: str = Path(..., description="The unique element ID of the relationship to delete."),
    tx: AsyncTransaction = Depends(get_db)
):
    """Delete a relationship by its unique element ID."""
    endpoint_name = f"DeleteRelationshipByID:{element_id}"
    query = "MATCH ()-[r]-() WHERE elementId(r) = $element_id DETACH DELETE r RETURN count(r) AS deleted_count"
    params = {"element_id": element_id}

    print(f"DEBUG ({endpoint_name}): Attempting to delete relationship with element ID: {element_id}")

    try:
        # Use tx.run() directly
        result: AsyncResult = await tx.run(query, params)
        # If DETACH DELETE is used, single() might return None even if deleted
        # Check the summary instead
        # record: Optional[Record] = await result.single()
        summary: ResultSummary = await result.consume()
        print(f"DEBUG ({endpoint_name}): Delete query executed. Summary: {summary.counters}")

        deleted_count = summary.counters.relationships_deleted

        if deleted_count == 1:
            print(f"INFO ({endpoint_name}): Relationship with element ID '{element_id}' deleted successfully.")
            # Return None for 204 status
            return None
        elif deleted_count == 0:
            # Relationship not found, but DELETE is idempotent, so return 204
            print(f"INFO ({endpoint_name}): Relationship with element ID '{element_id}' not found (idempotent delete).")
            return None
        else:
            # Should not happen with elementId
            print(f"WARN ({endpoint_name}): Unexpectedly deleted {deleted_count} relationships for element ID '{element_id}'.")
            # Still return success as *a* relationship was likely deleted
            return None

    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error during deletion - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error deleting relationship: {db_err.code}")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error during deletion - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during relationship deletion.") 