from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from neo4j import AsyncDriver, AsyncResult, Record, AsyncTransaction, exceptions as neo4j_exceptions, AsyncSession
from pydantic import ValidationError
from typing import List, Optional, Union, Dict, Any
import traceback
import functools
import datetime # Ensure datetime is imported
from datetime import timezone
import uuid
from collections.abc import Mapping # Add this import

# Logger setup (assuming standard logging)
import logging
logger = logging.getLogger(__name__)

# Database dependency
from src.db.neo4j_driver import get_db # , Neo4jSession # Removed - Alias doesn't exist

# Model Imports - CLEANED UP
from src.models.concept import (
    Concept, 
    ConceptCreate, 
    ConceptResponse, 
    ConceptUpdate
)
from src.models.path import PathResponse
from src.models.relationship import (
    RelationshipResponse, 
    RelationshipInfo, 
    TemporalRelationshipInfo, 
    SpatialRelationshipInfo
)

# Utility and Validation Imports
from src.validation.kantian_validator import KantianValidator, KantianValidationError
from src.cypher_queries import concept_queries, specialized_queries
from src.utils.converters import convert_neo4j_datetimes
from neo4j.time import DateTime as Neo4jDateTime
from neo4j.graph import Node # <-- Import Node

# Define the mapping locally
relationship_models_map: Dict[str, type] = {
    "PRECEDES": TemporalRelationshipInfo,
    "SPATIALLY_RELATES_TO": SpatialRelationshipInfo,
    # Add other specific relationship type strings mapped to their
    # corresponding Pydantic *Info or specialized models here.
    # If a type isn't listed, the default Relationship model will be used.
}

router = APIRouter()

# --- REMOVE Query Loading for Concepts ---
# QUERY_KEYS = [...] # Removed
# QUERIES = {} # Removed
# for key in QUERY_KEYS: # Removed
#    ... (loading logic removed) ...

# --- REMOVED Helper Function (moved to src/utils/converters.py) ---
# def convert_neo4j_datetimes(data: dict) -> dict:
#    ...

# --- NEW Endpoint: GET / (Handles Listing & Filtering) ---
@router.get(
    "/",
    response_model=List[ConceptResponse], # Use ConceptResponse
    summary="Retrieve Concepts (with optional filtering)",
    description="Retrieves a list of concepts. Allows filtering by category, subcategory, or minimum confidence score using query parameters.",
    tags=["Concepts"]
)
async def get_concepts(
    category_name: Optional[str] = Query(None, description="Filter by Kantian category name (e.g., Relation)."),
    subcategory_name: Optional[str] = Query(None, description="Filter by Kantian subcategory name (e.g., Causality)."),
    confidence_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score."),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of concepts to return."),
    skip: int = Query(0, ge=0, description="Number of concepts to skip (for pagination)."),
    tx: AsyncTransaction = Depends(get_db)
):
    """Handles fetching concepts with optional filters."""
    query_key = 'getConcepts' # Default
    query = concept_queries.GET_CONCEPTS # Use constant
    parameters = {"limit": limit, "skip": skip}
    endpoint_name = "GetConcepts"

    if category_name:
        query_key = 'getConceptsByCategory'
        query = concept_queries.GET_CONCEPTS_BY_CATEGORY # Use constant
        parameters["category"] = category_name
        endpoint_name += f"ByCategory:{category_name}"
    elif subcategory_name:
        query_key = 'getConceptsBySubcategory'
        query = concept_queries.GET_CONCEPTS_BY_SUBCATEGORY # Use constant
        parameters["subcategory"] = subcategory_name
        endpoint_name += f"BySubcategory:{subcategory_name}"
    elif confidence_threshold is not None:
        query_key = 'getConceptsByConfidence'
        query = concept_queries.GET_CONCEPTS_BY_CONFIDENCE # Use constant
        parameters["threshold"] = confidence_threshold
        endpoint_name += f"ByConfidence>={confidence_threshold}"

    try:
        # Directly use tx.run()
        result: AsyncResult = await tx.run(query, parameters)
        # Use result.data() which returns List[Dict[str, Any]]
        records_data: List[Dict] = await result.data()
        summary = await result.consume() # Consume the result
        logger.debug(f"({endpoint_name}): Query executed, {summary.counters}. Retrieved {len(records_data)} records.")

        validated_concepts = []
        # Iterate over the dictionaries directly
        for record_data in records_data:
            # record_data is already a dictionary, no need for .data()
            try:
                # Default to extracting the 'concept' map if present
                concept_data_to_validate = record_data.get('concept', record_data)

                if concept_data_to_validate:
                     # --- Convert Neo4j DateTime before validation ---
                    concept_data_native = convert_neo4j_datetimes(concept_data_to_validate)
                    validated_concepts.append(ConceptResponse.model_validate(concept_data_native))
                else:
                    logger.warning(f"({endpoint_name}): Record data could not be processed: {record_data}")

            except (ValidationError, KeyError, AttributeError) as val_err:
                 logger.error(f"({endpoint_name}): Validation/Processing failed for record: {record_data}. Error: {val_err}")
                 # Continue processing other records

        if not validated_concepts and records_data: # If validation failed for all records
             logger.error(f"({endpoint_name}): All records failed validation or processing.")
             # Optionally raise 500 if validation is critical and all failed
             # raise HTTPException(status_code=500, detail="Internal error processing concept data.")

        return validated_concepts # Return list of ConceptResponse

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error in {endpoint_name}: {e.code}")
    except HTTPException as http_err:
        raise http_err # Re-raise known HTTP exceptions
    except Exception as e: # Catch other unexpected errors
        logger.error(f"({endpoint_name}): Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error in {endpoint_name}")


# --- CRUD Endpoints ---

@router.post(
    "/",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new concept",
    tags=["Concepts"]
)
async def handle_create_concept(
    concept_in: ConceptCreate,
    tx: AsyncTransaction = Depends(get_db),
    validator: KantianValidator = Depends() # Inject validator
):
    """
    Handles the creation of a new concept node. Includes validation logic.
    Uses the injected AsyncTransaction directly.
    """
    endpoint_name = "Create Concept"
    logger.debug(f"({endpoint_name}): Received concept data: {concept_in.model_dump()}")

    # 1. Validate input data using KantianValidator
    try:
        # Use the correct validation method
        validator.validate_concept(concept_in.model_dump(exclude_unset=True))
        logger.debug(f"({endpoint_name}): Kantian validation passed for {concept_in.name}.")
    except KantianValidationError as e:
        logger.warning(f"({endpoint_name}): Kantian validation failed for {concept_in.name}: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e: # Catch unexpected validation errors
        logger.error(f"({endpoint_name}): Unexpected validation error for {concept_in.name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error during validation.")

    # 2. Prepare parameters for Cypher query
    params = concept_in.model_dump(exclude_unset=False)
    # Manually map 'confidence' from input model to 'confidence_score' for DB
    if 'confidence' in params:
        params['confidence_score'] = params.pop('confidence')
    else:
        # Ensure a default confidence_score is set if not provided
        params['confidence_score'] = 0.5 # Match ConceptCreate default

    # Directly use the imported constant
    query = concept_queries.CREATE_CONCEPT

    try:
        logger.debug(f"({endpoint_name}): Executing query with params: {params}")
        result: AsyncResult = await tx.run(query, params)
        record: Optional[Record] = await result.single() # Expecting one record
        summary = await result.consume() # Consume the result
        logger.debug(f"({endpoint_name}): Query executed. Summary: {summary.counters}")

        if record is None:
            logger.error(f"({endpoint_name}): Concept creation failed, no record returned.")
            raise HTTPException(status_code=500, detail="Concept creation failed in database.")

        # --- Convert Neo4j DateTime before validation ---
        created_data = record.data().get('c')
        if created_data:
             logger.debug(f"({endpoint_name}): Concept created successfully: {created_data}")
             # Use the helper function
             created_data_native = convert_neo4j_datetimes(created_data) # Pass the dict/map directly
             try:
                 # Now validate the converted data
                 created_concept = ConceptResponse.model_validate(created_data_native)
                 return created_concept
             except ValidationError as e:
                 logger.error(f"({endpoint_name}): Failed to validate created concept data returned from DB: {e}")
                 # Consider logging the problematic data: logger.debug(f"Data causing validation error: {created_data_native}") # Adjusted to logger.debug if uncommented
                 raise HTTPException(status_code=500, detail="Internal error validating created concept data.")
        else:
            logger.error(f"({endpoint_name}): Concept creation query did not return concept data ('c'). Record: {record.data()}")
            raise HTTPException(status_code=500, detail="Internal error: Failed to retrieve created concept.")

    except neo4j_exceptions.ConstraintError as e:
        logger.error(f"ConstraintError in {endpoint_name} for '{concept_in.name}': {e}")
        # Transaction context manager handles rollback on exception
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Concept with name '{concept_in.name}' already exists.")
    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error creating concept: {e.code}")
    except HTTPException as http_err:
        raise http_err # Re-raise HTTP exceptions from validation etc.
    except Exception as e:
        logger.error(f"({endpoint_name}): Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error creating concept.")

@router.get(
    "/{element_id}",
    response_model=ConceptResponse,
    summary="Get a specific concept by its element ID",
    tags=["Concepts"]
)
async def get_concept_by_id(
    element_id: str = Path(..., description="The element ID of the concept to retrieve."),
    tx: AsyncTransaction = Depends(get_db)
):
    """
    Retrieves a single concept by its Neo4j element ID.
    Uses the injected AsyncTransaction directly.
    """
    endpoint_name = f"Get Concept By ID ({element_id})"
    # Directly use the imported constant
    query = concept_queries.GET_CONCEPT_BY_ID

    parameters = {"element_id": element_id}

    try:
        logger.debug(f"({endpoint_name}): Executing query with params: {parameters}")
        result: AsyncResult = await tx.run(query, parameters)
        record: Optional[Record] = await result.single()
        summary = await result.consume()
        logger.debug(f"({endpoint_name}): Query executed. Summary: {summary.counters}")

        if record is None:
            logger.info(f"({endpoint_name}): Concept not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Concept with element ID '{element_id}' not found.")

        # --- Convert Neo4j DateTime before validation ---
        concept_data = record.data().get('c')
        if concept_data:
             logger.debug(f"({endpoint_name}): Found concept data: {concept_data}")
             # Use the helper function
             concept_data_native = convert_neo4j_datetimes(concept_data) # Pass the dict/map directly
             try:
                 # Validate the converted data
                 return ConceptResponse.model_validate(concept_data_native)
             except ValidationError as e:
                 logger.error(f"({endpoint_name}): Failed to validate concept data returned from DB: {e}")
                 # Consider logging the problematic data: logger.debug(f"Data causing validation error: {concept_data_native}") # Adjusted to logger.debug if uncommented
                 raise HTTPException(status_code=500, detail="Internal error validating concept data.")
        else:
             logger.error(f"({endpoint_name}): Query returned record but no concept data ('c'). Record: {record.data()}")
             raise HTTPException(status_code=500, detail="Internal error retrieving concept data.")

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error retrieving concept: {e.code}")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"({endpoint_name}): Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error retrieving concept.")

@router.patch(
    "/{element_id}",
    response_model=ConceptResponse,
    summary="Update a concept partially",
    tags=["Concepts"]
)
async def update_concept_partial(
    concept_update: ConceptUpdate, # Moved before element_id
    element_id: str = Path(..., description="The element ID of the concept to update."),
    tx: AsyncTransaction = Depends(get_db),
    validator: KantianValidator = Depends() # Inject validator
):
    """
    Partially updates a concept's properties based on the provided data.
    Uses the injected AsyncTransaction directly.
    Validates the update data.
    """
    endpoint_name = f"Update Concept ({element_id})"
    logger.debug(f"({endpoint_name}): Received update data: {concept_update.model_dump(exclude_unset=True)}")

    # 1. Exclude unset fields to only update provided values
    update_data = concept_update.model_dump(exclude_unset=True)

    if not update_data:
        logger.warning(f"({endpoint_name}): No update data provided.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")

    # 2. Validate the fields being updated
    try:
        # Use the correct validation method for the fields being updated
        validator.validate_concept(update_data) # Validate only the provided fields
        logger.debug(f"({endpoint_name}): Kantian validation passed for update data.")
    except KantianValidationError as e:
        logger.warning(f"({endpoint_name}): Kantian validation failed for update: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e: # Catch unexpected validation errors
        logger.error(f"({endpoint_name}): Unexpected validation error during update: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal error during update validation.")

    # 3. Prepare parameters for Cypher
    # Manually map 'confidence' from input model to 'confidence_score' for DB if present
    if 'confidence' in update_data:
        update_data['confidence_score'] = update_data.pop('confidence')

    params = {"element_id": element_id, "update_data": update_data}

    # Directly use the imported constant
    query = concept_queries.UPDATE_CONCEPT_PARTIAL

    try:
        logger.debug(f"({endpoint_name}): Executing query with params: {params}")
        result: AsyncResult = await tx.run(query, params)
        record: Optional[Record] = await result.single()
        summary = await result.consume()
        logger.debug(f"({endpoint_name}): Query executed. Summary: {summary.counters}")

        if record is None:
            logger.info(f"({endpoint_name}): Concept not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Concept with element ID '{element_id}' not found for update.")

        # --- Convert Neo4j DateTime before validation ---
        updated_data = record.data().get('c')
        if updated_data:
            logger.debug(f"({endpoint_name}): Updated concept data: {updated_data}")
            # Use the helper function
            updated_data_native = convert_neo4j_datetimes(updated_data) # Pass the dict/map directly
            try:
                 # Validate the converted data
                 return ConceptResponse.model_validate(updated_data_native)
            except ValidationError as e:
                 logger.error(f"({endpoint_name}): Failed to validate updated concept data returned from DB: {e}")
                 # Consider logging the problematic data: logger.debug(f"Data causing validation error: {updated_data_native}") # Adjusted to logger.debug if uncommented
                 raise HTTPException(status_code=500, detail="Internal error validating updated concept data.")
        else:
             logger.error(f"({endpoint_name}): Update query returned record but no concept data ('c'). Record: {record.data()}")
             raise HTTPException(status_code=500, detail="Internal error retrieving updated concept.")

    except neo4j_exceptions.ConstraintError as e:
         # Handle potential constraint errors if name is updated to an existing one
         logger.error(f"ConstraintError in {endpoint_name}: {e}")
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Update failed due to constraint: {e}")
    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error updating concept: {e.code}")
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"({endpoint_name}): Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error updating concept.")

@router.delete(
    "/{element_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a concept by its element ID",
    tags=["Concepts"]
)
async def delete_concept(
    element_id: str = Path(..., description="The element ID of the concept to delete."),
    tx: AsyncTransaction = Depends(get_db)
):
    """
    Deletes a concept node and any relationships connected to it.
    Returns 204 No Content on success, including if the concept didn't exist.
    Uses the injected AsyncTransaction directly.
    """
    endpoint_name = f"Delete Concept ({element_id})"
    # Directly use the imported constant
    query = concept_queries.DELETE_CONCEPT

    parameters = {"element_id": element_id}

    try:
        logger.debug(f"({endpoint_name}): Executing query with params: {parameters}")
        result: AsyncResult = await tx.run(query, parameters)
        summary = await result.consume()
        logger.debug(f"({endpoint_name}): Query executed. Summary: {summary.counters}")

        # Check if any nodes were deleted. If not, the concept didn't exist (which is fine for DELETE).
        nodes_deleted = summary.counters.nodes_deleted
        logger.info(f"({endpoint_name}): Nodes deleted: {nodes_deleted}")

        # No need to check if the record exists. DELETE is idempotent.
        # If the node existed, it's deleted. If not, the operation effectively does nothing.
        return None # FastAPI handles the 204 response automatically for None body

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error deleting concept: {e.code}")
    except Exception as e:
        logger.error(f"({endpoint_name}): Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error deleting concept.")


# --- Routes MOVED from relationships.py ---
# Ensure paths start with /{concept_id}/...

@router.get(
    "/{concept_id}/properties",
    response_model=List[ConceptResponse], # Use ConceptResponse
    summary="Get Properties of a Concept",
    description="Retrieves concepts that are properties (accidents) of a given concept (substance), linked via HAS_PROPERTY relationship.",
    tags=["Relationships"] # Keep tag? Or move to Concepts? Let's keep for now.
)
async def get_concept_properties(
    concept_id: str = Path(..., title="Concept Element ID", description="Use element ID"),
    limit: int = Query(50, ge=1, le=100),
    tx: AsyncTransaction = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Properties for '{concept_id}'"
    # Use the constant
    query = concept_queries.GET_CONCEPT_PROPERTIES

    try:
        result = await tx.run(query, parameters)
        # Use result.data() which returns List[Dict[str, Any]]
        records_data: List[Dict] = await result.data()
        await result.consume()

        validated_props = []
        # Iterate over the dictionaries directly
        for record_data in records_data:
             prop_data = record_data.get('prop')
             if prop_data:
                 try:
                     # --- Convert Neo4j DateTime before validation ---
                     prop_data_native = convert_neo4j_datetimes(prop_data)
                     validated_props.append(ConceptResponse.model_validate(prop_data_native))
                 except (ValidationError, KeyError, AttributeError) as val_err:
                     logger.error(f"({endpoint_name}): Validation/Processing failed for property record: {prop_data}. Error: {val_err}")
             else:
                 logger.warning(f"({endpoint_name}): Record missing 'prop' key: {record_data}")

        return validated_props

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting properties: {e.code}")
    except Exception as e:
        logger.error(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error getting properties.")


@router.get(
    "/{concept_id}/causal-chain",
    response_model=List[PathResponse], # The response is a list of paths
    summary="Get Causal Chain from a Concept",
    description="Retrieves causal chains (paths) starting from a given concept, up to a specified depth.",
    tags=["Relationships"]
)
async def get_causal_chain(
    concept_id: str = Path(..., title="Concept Element ID", description="Use element ID"),
    max_depth: int = Query(3, ge=1, le=5), result_limit: int = Query(10, ge=1, le=50),
    tx: AsyncTransaction = Depends(get_db)
):
    # Prepare parameters for the query
    parameters = {"conceptId": concept_id, "resultLimit": result_limit}
    endpoint_name = f"Causal Chain for '{concept_id}'"

    # Get the base query string
    base_query = specialized_queries.GET_CAUSAL_CHAIN

    # --- Format max_depth into the query string using .format() ---
    formatted_query = base_query.format(max_depth=max_depth) # Use .format for {max_depth}
    # -----------------------------------------------------------

    try:
        logger.debug(f"({endpoint_name}): Executing query: {formatted_query} with params: {parameters}") # Log formatted query
        result: AsyncResult = await tx.run(formatted_query, parameters)

        # Get results as a list of dictionaries
        records_data: List[Dict] = await result.data()
        summary = await result.consume()
        logger.debug(f"({endpoint_name}): Query executed, {summary.counters}. Retrieved {len(records_data)} records.")

        validated_paths = []
        # Each record_dict should now contain {'nodes': [...], 'relationships': [...]} keys
        for record_dict in records_data:
            try:
                # Convert datetimes within the nested lists of nodes and relationships
                converted_record = convert_neo4j_datetimes(record_dict)

                # Directly validate the dictionary against PathResponse
                # This assumes the structure from the Cypher query matches the model
                # (List of node dicts, List of relationship dicts)
                if converted_record and 'nodes' in converted_record and 'relationships' in converted_record:
                    validated_path = PathResponse.model_validate(converted_record)
                    validated_paths.append(validated_path)
                else:
                     logger.warning(f"({endpoint_name}): Record dict missing 'nodes' or 'relationships' key after conversion: {converted_record}")

            except (ValidationError, KeyError, AttributeError, TypeError) as e:
                logger.error(f"Error processing path record dict: {record_dict}. Error: {e}")
                # Optionally, log the converted_record too if validation fails after conversion
                # logger.debug(f"Converted data causing validation error: {converted_record}") # Adjusted to logger.debug

        return validated_paths

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting causal chain: {e.code}")
    except Exception as e:
        logger.error(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error getting causal chain.")


@router.get(
    "/{concept_id}/relationships",
    response_model=List[RelationshipResponse],
    summary="Get All Relationships for a Concept",
    tags=["concepts", "relationships"]
)
async def get_all_relationships_for_concept(
    concept_id: str = Path(..., description="Element ID of the concept"),
    skip: int = Query(0, ge=0, description="Number of relationships to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of relationships to return"),
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type (case-sensitive)"),
    tx: AsyncTransaction = Depends(get_db),
) -> List[RelationshipResponse]: # Changed base to RelationshipResponse
    """
    Retrieves all incoming and outgoing relationships for a specific concept.
    Returns a list of relationships conforming to the RelationshipResponse schema.
    """
    query = specialized_queries.GET_ALL_RELATIONSHIPS_FOR_CONCEPT
    parameters = {"conceptId": concept_id, "skip": skip, "limit": limit}
    relationships = [] # Initialize relationships list
    try:
        result = await tx.run(query, parameters)
        record_count = 0
        async for record in result:
            record_count += 1
            try:
                rel_map = record.get("relMap")
                start_node_data = record.get("startNode")
                end_node_data = record.get("endNode")

                # Corrected structural and type checks
                if not all([
                    isinstance(rel_map, dict),
                    isinstance(start_node_data, Node),
                    isinstance(end_node_data, Node)
                ]):
                    logger.warning(f"Skipping record due to unexpected data structure: {record.data()}")
                    continue

                # Now access node properties using .get() or attribute access
                start_node_id = start_node_data.element_id
                start_node_name = start_node_data.get('name')
                end_node_id = end_node_data.element_id
                end_node_name = end_node_data.get('name')
                rel_element_id = rel_map.get("elementId")
                rel_type_str = rel_map.get("type")

                if not rel_type_str or not rel_element_id:
                    logger.warning(f"Skipping record due to missing type or elementId: {record.data()}")
                    continue

                # Prepare properties, converting timestamps
                properties = dict(rel_map.get("properties", {}))
                for key in ["created_at", "updated_at"]:
                    timestamp_val = properties.get(key)
                    if isinstance(timestamp_val, Neo4jDateTime):
                        properties[key] = timestamp_val.to_native().replace(tzinfo=timezone.utc)
                    elif isinstance(timestamp_val, str):
                        try: properties[key] = datetime.datetime.fromisoformat(timestamp_val).replace(tzinfo=timezone.utc)
                        except ValueError: pass # Keep original string

                # Always prepare data for RelationshipResponse model
                rel_info = {
                    "elementId": rel_element_id,
                    "source_id": start_node_id,
                    "target_id": end_node_id,
                    "type": rel_type_str,
                    "properties": properties,
                    "source_name": start_node_name,
                    "target_name": end_node_name,
                }

                # Validate and append using RelationshipResponse
                validated_rel = RelationshipResponse(**rel_info)
                relationships.append(validated_rel)
                # logger.debug(f"Processed relationship: {rel_element_id} Type: {rel_type_str} using RelationshipResponse") # Adjusted comment

            except ValidationError as e:
                logger.error(f"Validation error processing relationship record: {record.data()}. Model: RelationshipResponse. Error: {e}")
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                logger.error(f"Data processing error for record: {record.data()}. Error: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error processing record: {record.data()}. Error: {e}")

        # Consume the result summary after iterating
        summary = await result.consume()
        logger.info(f"Processed {record_count} relationship records for concept ID {concept_id}. Query Summary: {summary}")
        if record_count == 0:
             logger.info(f"No relationships found or processed for concept ID: {concept_id}")

        return relationships

    except Exception as e:
        logger.exception(f"Database error retrieving relationships for concept {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get(
    "/{concept_id}/hierarchy",
    response_model=List[ConceptResponse], # Assuming it returns concepts
    summary="Get Concept Hierarchy",
    description="Retrieves the hierarchy (parents/children) related to a concept via IS_A relationships.",
    tags=["Relationships"]
)
async def get_concept_hierarchy(
    concept_id: str = Path(..., title="Concept Element ID", description="Use element ID"),
    limit: int = Query(50, ge=1, le=100),
    tx: AsyncTransaction = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "resultLimit": limit}
    endpoint_name = f"Hierarchy for '{concept_id}'"
    max_depth_val = 3 # Define max depth (can be made a parameter later)
    
    # Use the constant from specialized_queries module
    query_template = specialized_queries.GET_CONCEPT_HIERARCHY
    # Format the max_depth into the query string
    query = query_template.format(max_depth=max_depth_val)

    try:
        result = await tx.run(query, parameters)
        # Correct way to fetch records asynchronously
        records = [record async for record in result]
        await result.consume()

        # Assuming query returns related concept nodes aliased as 'relatedConcept'
        concepts = []
        for record in records:
             concept_data = record.data().get('relatedConcept')
             if concept_data:
                 try:
                      # --- Convert Neo4j DateTime before validation ---
                     concept_data_native = convert_neo4j_datetimes(concept_data)
                     concepts.append(ConceptResponse.model_validate(concept_data_native))
                 except (ValidationError, KeyError, AttributeError) as val_err:
                      logger.error(f"({endpoint_name}): Validation/Processing failed for hierarchy record: {concept_data}. Error: {val_err}")
             else:
                 logger.warning(f"({endpoint_name}): Record missing 'relatedConcept' key: {record.data()}")
        return concepts

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting hierarchy: {e.code}")
    except Exception as e:
        logger.error(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error getting hierarchy.")


@router.get(
    "/{concept_id}/membership",
    response_model=List[ConceptResponse], # Assuming it returns group/category concepts
    summary="Get Concept Membership",
    description="Retrieves groups or categories a concept belongs to via MEMBER_OF relationships.",
    tags=["Relationships"]
)
async def get_concept_membership(
    concept_id: str = Path(..., title="Concept Element ID", description="Use element ID"),
    limit: int = Query(50, ge=1, le=100),
    tx: AsyncTransaction = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "resultLimit": limit}
    endpoint_name = f"Membership for '{concept_id}'"
    max_depth_val = 3 # Define max depth
    
    # Use the constant from specialized_queries module
    query_template = specialized_queries.GET_CONCEPT_MEMBERSHIP
    # Format the max_depth into the query string
    query = query_template.format(max_depth=max_depth_val)

    try:
        result = await tx.run(query, parameters)
        # Correct way to fetch records asynchronously
        records = [record async for record in result]
        await result.consume()

        # Assuming query returns group/category concept nodes aliased as 'group'
        groups = []
        for record in records:
             group_data = record.data().get('group')
             if group_data:
                 try:
                     # --- Convert Neo4j DateTime before validation ---
                     group_data_native = convert_neo4j_datetimes(group_data)
                     groups.append(ConceptResponse.model_validate(group_data_native))
                 except (ValidationError, KeyError, AttributeError) as val_err:
                      logger.error(f"({endpoint_name}): Validation/Processing failed for membership record: {group_data}. Error: {val_err}")
             else:
                 logger.warning(f"({endpoint_name}): Record missing 'group' key: {record.data()}")
        return groups

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting membership: {e.code}")
    except Exception as e:
        logger.error(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error getting membership.")


@router.get(
    "/{concept_id}/interacting",
    response_model=List[ConceptResponse],
    summary="Get Interacting Concepts",
    description="Retrieves concepts that interact with the given concept via INTERACTS_WITH relationships.",
    tags=["Relationships"]
)
async def get_interacting_concepts(
    concept_id: str = Path(..., title="Concept Element ID", description="Use element ID"),
    limit: int = Query(50, ge=1, le=100),
    tx: AsyncTransaction = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Interacting Concepts for '{concept_id}'"
    
    # Use the constant from specialized_queries module
    query = specialized_queries.GET_INTERACTING_CONCEPTS

    try:
        result = await tx.run(query, parameters)
        # Correct way to fetch records asynchronously
        records = [record async for record in result]
        await result.consume()

        # Assuming query returns interacting concept nodes aliased as 'interactingConcept'
        concepts = []
        for record in records:
             concept_data = record.data().get('interactingConcept')
             if concept_data:
                 try:
                     # --- Convert Neo4j DateTime before validation ---
                     concept_data_native = convert_neo4j_datetimes(concept_data)
                     concepts.append(ConceptResponse.model_validate(concept_data_native))
                 except (ValidationError, KeyError, AttributeError) as val_err:
                     logger.error(f"({endpoint_name}): Validation/Processing failed for interaction record: {concept_data}. Error: {val_err}")
             else:
                 logger.warning(f"({endpoint_name}): Record missing 'interactingConcept' key: {record.data()}")
        return concepts

    except neo4j_exceptions.Neo4jError as e:
        logger.error(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error getting interacting concepts: {e.code}")
    except Exception as e:
        logger.error(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error getting interacting concepts.")


@router.get(
    "/{concept_id}/temporal",
    response_model=List[TemporalRelationshipInfo],
    summary="Get Temporal Relationships",
    description="Retrieves temporal relationships (TEMPORALLY_RELATES_TO) connected to the concept.",
    tags=["Relationships"]
)
async def get_temporal_relationships(
    concept_id: str = Path(..., description="Element ID of the concept"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of relationships to return"),
    tx: AsyncTransaction = Depends(get_db),
) -> List[TemporalRelationshipInfo]:
    """
    Retrieves temporal relationships (PRECEDES) for a specific concept.
    # Corrected: Returns a list containing info about the related concept and the relationship.
    """
    query = specialized_queries.GET_TEMPORAL_RELATIONSHIPS
    parameters = {"conceptId": concept_id, "limit": limit}
    relationships = []

    try:
        result = await tx.run(query, parameters)
        record_count = 0
        async for record in result:
            record_count += 1
            rel_info_for_model = {} # Define outside try block for error logging
            try:
                rel_map = record.get("relMap")
                related_concept_map = record.get("relatedConcept") # Map {.*, elementId}
                start_node = record.get("startNode")             # Node object
                end_node = record.get("endNode")                 # Node object

                # Type checks: Check Mapping for maps, Node for nodes
                if not all([
                    isinstance(rel_map, Mapping),
                    isinstance(related_concept_map, Mapping),
                    isinstance(start_node, Node), # Check for Node type
                    isinstance(end_node, Node)    # Check for Node type
                ]):
                    logger.warning(f"Skipping temporal record due to unexpected data types: {record.data()}")
                    continue

                rel_type_str = rel_map.get("type")
                if rel_type_str != "PRECEDES":
                     logger.warning(f"Skipping non-PRECEDES record in temporal endpoint: {record.data()}")
                     continue

                # Determine direction using Node element IDs
                start_node_id = start_node.element_id # Access Node property
                end_node_id = end_node.element_id     # Access Node property

                direction = "unknown"
                if start_node_id == concept_id:
                    direction = "outgoing"
                    # related_concept is end_node
                elif end_node_id == concept_id:
                    direction = "incoming"
                    # related_concept is start_node
                else:
                     logger.warning(f"Could not determine direction for temporal relationship: {record.data()}")
                     continue # Skip if direction is unclear

                # Prepare properties (accessing dicts)
                properties = dict(rel_map.get("properties", {}))
                # Convert timestamps
                for key in ["created_at", "updated_at"]:
                    timestamp_val = properties.get(key)
                    if isinstance(timestamp_val, Neo4jDateTime):
                        properties[key] = timestamp_val.to_native().replace(tzinfo=timezone.utc)
                    elif isinstance(timestamp_val, str):
                         try: properties[key] = datetime.datetime.fromisoformat(timestamp_val).replace(tzinfo=timezone.utc)
                         except ValueError: pass # Keep original string
                # Add temporal distance from record top level
                temporal_distance = record.get("temporalDistance")
                if temporal_distance is not None:
                    try: properties["temporal_distance"] = float(temporal_distance)
                    except (ValueError, TypeError): logger.warning(f"Could not convert temporal distance '{temporal_distance}'")

                # Prepare data for TemporalRelationshipInfo model correctly (using related_concept_map)
                rel_info_for_model = {
                    "elementId": rel_map.get("elementId"), # <-- ADDED from rel_map
                    "related_concept_id": related_concept_map.get("elementId"), # Get ID from map
                    "related_concept_name": related_concept_map.get("name"),   # Get name from map
                    "relationship_type": rel_type_str,
                    "direction": direction,
                    "properties": properties,
                }

                # Validate and append
                validated_rel = TemporalRelationshipInfo(**rel_info_for_model)
                relationships.append(validated_rel)
                # logger.debug(f"Processed temporal relationship: {direction} {rel_type_str} {validated_rel.related_concept_name}")

            except ValidationError as e:
                logger.error(f"Validation error for TemporalRelationshipInfo: Data={rel_info_for_model}. Error: {e}")
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                 logger.error(f"Data processing error for temporal record: {record.data()}. Error: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error processing temporal record: {record.data()}. Error: {e}")

        summary = await result.consume()
        logger.info(f"Processed {record_count} temporal relationship records for concept ID {concept_id}. Query Summary: {summary}")
        if record_count == 0:
             logger.info(f"No temporal relationships found or processed for concept ID: {concept_id}")
        return relationships

    except Exception as e:
        logger.exception(f"Database error retrieving temporal relationships for concept {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.get(
    "/{concept_id}/spatial",
    response_model=List[SpatialRelationshipInfo],
    summary="Get Spatial Relationships",
    description="Retrieves spatial relationships (SPATIALLY_RELATES_TO) connected to the concept.",
    tags=["Relationships"]
)
async def get_spatial_relationships(
    concept_id: str = Path(..., description="Element ID of the concept"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of relationships to return"),
    tx: AsyncTransaction = Depends(get_db),
) -> List[SpatialRelationshipInfo]:
    """
    Retrieves spatial relationships (SPATIALLY_RELATES_TO) for a specific concept.
    # Corrected: Returns a list containing info about the related concept and the relationship.
    """
    query = specialized_queries.GET_SPATIAL_RELATIONSHIPS
    parameters = {"conceptId": concept_id, "limit": limit}
    relationships = []

    try:
        result = await tx.run(query, parameters)
        record_count = 0
        async for record in result:
            record_count += 1
            rel_info_for_model = {} # Define outside try block for error logging
            try:
                rel_map = record.get("relMap")
                related_concept_map = record.get("relatedConcept") # Map {.*, elementId}
                start_node = record.get("startNode")             # Node object
                end_node = record.get("endNode")                 # Node object

                # Type checks: Check Mapping for maps, Node for nodes
                if not all([
                    isinstance(rel_map, Mapping),
                    isinstance(related_concept_map, Mapping),
                    isinstance(start_node, Node), # Check for Node type
                    isinstance(end_node, Node)    # Check for Node type
                ]):
                    logger.warning(f"Skipping spatial record due to unexpected data types: {record.data()}")
                    continue

                rel_type_str = rel_map.get("type")
                if rel_type_str != "SPATIALLY_RELATES_TO":
                     logger.warning(f"Skipping non-SPATIALLY_RELATES_TO record in spatial endpoint: {record.data()}")
                     continue

                # Determine direction using Node element IDs
                start_node_id = start_node.element_id # Access Node property
                end_node_id = end_node.element_id     # Access Node property

                direction = "unknown"
                if start_node_id == concept_id:
                    direction = "outgoing"
                    # related_concept is end_node
                elif end_node_id == concept_id:
                    direction = "incoming"
                    # related_concept is start_node
                else:
                     logger.warning(f"Could not determine direction for spatial relationship: {record.data()}")
                     continue # Skip if direction is unclear

                # Prepare properties (accessing dicts)
                properties = dict(rel_map.get("properties", {}))
                # Convert timestamps
                for key in ["created_at", "updated_at"]:
                     timestamp_val = properties.get(key)
                     if isinstance(timestamp_val, Neo4jDateTime):
                         properties[key] = timestamp_val.to_native().replace(tzinfo=timezone.utc)
                     elif isinstance(timestamp_val, str):
                         try: properties[key] = datetime.datetime.fromisoformat(timestamp_val).replace(tzinfo=timezone.utc)
                         except ValueError: pass # Keep original string
                # Convert distance
                distance = properties.get("distance") # Distance is already in properties from relMap
                if distance is not None:
                    try: properties["distance"] = float(distance)
                    except (ValueError, TypeError): logger.warning(f"Could not convert spatial distance '{distance}'")
                # Add relationType from record top level into properties for validation
                relationType = record.get("relationType")
                if relationType is not None: properties["relation_type"] = relationType

                # Prepare data for SpatialRelationshipInfo model correctly (using related_concept_map)
                rel_info_for_model = {
                    "elementId": rel_map.get("elementId"), # <-- ADDED from rel_map
                    "related_concept_id": related_concept_map.get("elementId"), # Get ID from map
                    "related_concept_name": related_concept_map.get("name"),   # Get name from map
                    "relationship_type": rel_type_str,
                    "direction": direction,
                    "properties": properties,
                }

                # Validate and append
                validated_rel = SpatialRelationshipInfo(**rel_info_for_model)
                relationships.append(validated_rel)
                # logger.debug(f"Processed spatial relationship: {direction} {rel_type_str} {validated_rel.related_concept_name}")

            except ValidationError as e:
                logger.error(f"Validation error for SpatialRelationshipInfo: Data={rel_info_for_model}. Error: {e}")
            except (AttributeError, TypeError, ValueError, KeyError) as e:
                 logger.error(f"Data processing error for spatial record: {record.data()}. Error: {e}")
            except Exception as e:
                logger.exception(f"Unexpected error processing spatial record: {record.data()}. Error: {e}")

        summary = await result.consume()
        logger.info(f"Processed {record_count} spatial relationship records for concept ID {concept_id}. Query Summary: {summary}")
        if record_count == 0:
             logger.info(f"No spatial relationships found or processed for concept ID: {concept_id}")
        return relationships

    except Exception as e:
        logger.exception(f"Database error retrieving spatial relationships for concept {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error")