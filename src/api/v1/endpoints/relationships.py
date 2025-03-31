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
# --- Import Cypher query constants --- #
from src.cypher_queries.relationship_queries import (
    LIST_RELATIONSHIPS, COUNT_RELATIONSHIPS, CREATE_RELATIONSHIP, 
    CHECK_NODE_EXISTS, GET_RELATIONSHIP_BY_ID, UPDATE_RELATIONSHIP,
    CHECK_RELATIONSHIP_EXISTS, DELETE_RELATIONSHIP
)

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
        # Build where clause if type filter is provided
        where_clause = ""
        parameters = {}
        if type:
            where_clause = "WHERE toUpper(type(rel)) = toUpper($rel_type)"
            parameters["rel_type"] = type

        # Format queries with where clause
        list_query = LIST_RELATIONSHIPS.format(where_clause=where_clause)
        count_query = COUNT_RELATIONSHIPS.format(where_clause=where_clause)
        
        # Add pagination parameters
        list_parameters = {**parameters, "skip": skip, "limit": limit}
        count_parameters = parameters  # Use the same base parameters

        # Execute list query directly using tx.run()
        print(f"DEBUG ({endpoint_name}): Executing list query: {list_query} with params: {list_parameters}")
        list_result: AsyncResult = await tx.run(list_query, list_parameters)
        records_data: List[Dict] = await list_result.data()  # Fetch data as list of dictionaries
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
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Relationship",
    description="Creates a new relationship between two existing concepts after validation.",
    tags=["Relationships"]
)
async def handle_create_relationship(
    rel_in: RelationshipCreate,
    tx: AsyncTransaction = Depends(get_db)
):
    """Handles the creation of a new relationship."""
    endpoint_name = "CreateRelationship"
    try:
        # 1. Perform Kantian Validation
        props_to_validate = rel_in.properties.model_dump(exclude_unset=True)
        KantianValidator.validate_relationship(rel_in.type, props_to_validate)
        print(f"DEBUG ({endpoint_name}): Kantian validation passed for type {rel_in.type}.")

        # 2. Prepare parameters and query
        source_id = rel_in.source_id
        target_id = rel_in.target_id
        rel_type = rel_in.type
        
        # Prepare properties with timestamps
        properties = rel_in.properties.model_dump(exclude_unset=False)
        properties["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        properties["updated_at"] = properties["created_at"]  # Set updated_at on creation
        final_properties = {k: v for k, v in properties.items() if v is not None}

        # Format the CREATE query with the relationship type
        query = CREATE_RELATIONSHIP.format(rel_type=rel_type)
        
        # Prepare parameters
        tx_params = {
            "source_id": source_id,
            "target_id": target_id,
            "properties": final_properties,
        }

        # 3. Execute Write Transaction
        print(f"DEBUG ({endpoint_name}): Executing query: {query} with params: {tx_params}")
        result: AsyncResult = await tx.run(query, tx_params)
        record: Optional[Record] = await result.single()
        summary: ResultSummary = await result.consume()
        print(f"DEBUG ({endpoint_name}): Query executed. Summary: {summary.counters}")

        # Check if the relationship was created and data returned
        if record and summary.counters.relationships_created == 1:
            created_rel_data = record.data()
            print(f"DEBUG ({endpoint_name}): Relationship created successfully: {created_rel_data}")
            return RelationshipResponse.model_validate(created_rel_data)
        elif record is None and summary.counters.relationships_created == 0:
            # Check if nodes were found before concluding it's a 404
            source_exists_res = await tx.run(CHECK_NODE_EXISTS, {"id": source_id})
            source_exists = (await source_exists_res.single())['exists']
            await source_exists_res.consume()
            target_exists_res = await tx.run(CHECK_NODE_EXISTS, {"id": target_id})
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
        raise exc
    except HTTPException as http_err:
        raise http_err
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR ({endpoint_name}): Pydantic validation failed for DB result: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing created relationship.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

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
    params = {"element_id": element_id}

    print(f"DEBUG ({endpoint_name}): Executing query: {GET_RELATIONSHIP_BY_ID} with params: {params}")

    try:
        result: AsyncResult = await tx.run(GET_RELATIONSHIP_BY_ID, params)
        # Fetch all records instead of expecting a single one
        records: List[Record] = await result.data() 
        summary = await result.consume() # Consume after fetching data
        print(f"DEBUG ({endpoint_name}): Query executed. Fetched {len(records)} record(s). Summary: {summary.counters}")

        if len(records) == 0:
            # No relationship found
            detail = f"Relationship with element ID '{element_id}' not found."
            print(f"INFO ({endpoint_name}): {detail}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail
            )
        elif len(records) == 1:
            # Exactly one relationship found, proceed as before
            record = records[0]
            # Validate the returned data
            rel_data = record # record.data() is not needed as .data() was called on result
            print(f"DEBUG ({endpoint_name}): Relationship found: {rel_data}")
            return RelationshipResponse.model_validate(rel_data)
        else:
            # More than one relationship found - this should not happen with elementId!
            error_detail = f"Unexpectedly found {len(records)} relationships with element ID '{element_id}'."
            print(f"ERROR ({endpoint_name}): {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error: Inconsistent relationship data found."
            )

    except HTTPException as http_exc:
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
        update_payload = {}  # No properties to update
    else:
        # Get properties to update, excluding None values
        update_payload = update_data.properties.model_dump(exclude_unset=True)

    # Prevent updating with an empty properties dictionary
    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No properties provided for update."
        )

    # Add updated_at timestamp
    update_payload["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Build SET clauses dynamically
    set_clauses = []
    for key, value in update_payload.items():
        set_clauses.append(f"r.{key} = ${key}")
    set_statement = "SET " + ", ".join(set_clauses)

    # Format the UPDATE query with the SET statement
    query = UPDATE_RELATIONSHIP.format(set_statement=set_statement)
    
    # Combine ID and update data
    params = {"element_id": element_id, **update_payload}

    print(f"DEBUG ({endpoint_name}): Executing update query: {query} with params: {params}")

    try:
        # Run the query
        result: AsyncResult = await tx.run(query, params)
        # Fetch all records instead of expecting a single one
        records: List[Record] = await result.data()
        summary = await result.consume() # Consume after fetching data
        print(f"DEBUG ({endpoint_name}): Update query executed. Fetched {len(records)} record(s). Summary: {summary.counters}")

        if len(records) == 1 and summary.counters.properties_set > 0:
            # Exactly one record returned and properties were set
            record = records[0]
            updated_rel_data = record # record.data() not needed as result.data() was used
            # Convert datetimes before validation
            if 'properties' in updated_rel_data and updated_rel_data['properties']:
                converted_properties = convert_neo4j_datetimes(updated_rel_data['properties'])
                updated_rel_data['properties'] = converted_properties
            else:
                converted_properties = {}

            # Perform Kantian validation after getting the type and updated props
            try:
                KantianValidator.validate_relationship(updated_rel_data['type'], converted_properties)
                print(f"DEBUG ({endpoint_name}): Kantian validation passed for updated properties.")
            except KantianValidationError as val_err:
                print(f"ERROR ({endpoint_name}): Kantian validation failed AFTER update: {val_err}")
                # Although the DB update succeeded, validation failed. We might consider reverting,
                # but for now, return an error indicating the validation issue.
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Update successful but failed validation: {val_err}")

            print(f"DEBUG ({endpoint_name}): Relationship updated successfully: {updated_rel_data}")
            return RelationshipResponse.model_validate(updated_rel_data)

        elif len(records) == 0 and summary.counters.properties_set == 0:
            # No relationship found (query returned 0 records, no properties set)
            detail = f"Relationship with element ID '{element_id}' not found for update."
            print(f"INFO ({endpoint_name}): {detail}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
            
        elif len(records) > 1:
            # More than one relationship found - this should not happen with elementId!
            error_detail = f"Unexpectedly found {len(records)} relationships matching element ID '{element_id}' during update."
            print(f"ERROR ({endpoint_name}): {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error: Inconsistent relationship data found during update."
            )
            
        else:
            # Other unexpected cases (e.g., record found but no properties set, or vice versa)
            error_detail = f"Update failed unexpectedly. Records found: {len(records)}, Properties set: {summary.counters.properties_set}, Summary: {summary}"
            print(f"ERROR ({endpoint_name}): {error_detail}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during relationship update.")

    except KantianValidationError as exc:
        # This catches validation errors *before* the DB update (e.g., in payload)
        print(f"ERROR ({endpoint_name}): Kantian validation failed - {exc}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except HTTPException as http_exc:
        raise http_exc
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error updating relationship: {db_err.code}")
    except ValidationError as pydantic_err:
        print(f"ERROR ({endpoint_name}): Pydantic validation failed for updated DB result: {pydantic_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error processing updated relationship data.")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred updating the relationship.")

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
    """Deletes a relationship by its element ID, returning 404 if not found."""
    endpoint_name = f"DeleteRelationship:{element_id}"
    try:
        # 1. Check if the relationship exists first
        check_result: AsyncResult = await tx.run(CHECK_RELATIONSHIP_EXISTS, {"element_id": element_id})
        exists_record: Optional[Record] = await check_result.single()
        await check_result.consume()

        if not exists_record or not exists_record["exists"]:
            print(f"INFO ({endpoint_name}): Relationship not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Relationship with elementId '{element_id}' not found.")

        # 2. If it exists, delete it
        print(f"DEBUG ({endpoint_name}): Executing delete query: {DELETE_RELATIONSHIP}")
        delete_result: AsyncResult = await tx.run(DELETE_RELATIONSHIP, {"element_id": element_id})
        summary: ResultSummary = await delete_result.consume()
        print(f"DEBUG ({endpoint_name}): Delete query executed. Summary: {summary.counters}")

        if summary.counters.relationships_deleted == 1:
            print(f"INFO ({endpoint_name}): Relationship deleted successfully.")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            print(f"WARNING ({endpoint_name}): Relationship existed but was not deleted. Summary: {summary}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete relationship after existence check.")

    except HTTPException as http_err:
        raise http_err
    except neo4j_exceptions.Neo4jError as db_err:
        print(f"ERROR ({endpoint_name}): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during relationship deletion: {db_err.code}")
    except Exception as e:
        print(f"ERROR ({endpoint_name}): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during relationship deletion.")