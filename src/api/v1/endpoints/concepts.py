from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from neo4j import AsyncDriver, AsyncResult, Record, AsyncTransaction, exceptions as neo4j_exceptions, AsyncSession
from pydantic import ValidationError
from typing import List, Optional, Union
import traceback
import functools

from src.db.neo4j_driver import get_db
from src.models.concept import Concept, ConceptCreate, ConceptResponse, ConceptUpdate
from src.models.path import PathResponse
from src.utils.cypher_loader import load_query
from src.models.relationship import RelationshipInfo, TemporalRelationshipInfo, SpatialRelationshipInfo
from src.validation.kantian_validator import KantianValidator, KantianValidationError

router = APIRouter()

# --- Load Queries (Combine from both files, ensure unique keys) ---
QUERY_KEYS = [
    'getConcepts',
    'getConceptsByCategory',
    'getConceptsBySubcategory',
    'getConceptsByConfidence',
    'getConceptProperties',
    'getCausalChain',
    'getAllRelationshipsForConcept',
    'getConceptHierarchy',
    'getConceptMembership',
    'getInteractingConcepts',
    'getTemporalRelationships',
    'getSpatialRelationships'
]
QUERIES = {}
for key in QUERY_KEYS:
    try:
        QUERIES[key] = load_query(key)
        print(f"INFO: Query '{key}' loaded successfully.")
    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR loading query '{key}': {e}")
        QUERIES[key] = None

# --- Helper Function for Async Query Execution (MODIFIED) ---
async def _execute_read_query_async(
    session: AsyncSession, # MODIFIED: Accept session directly
    query: str,
    parameters: dict,
    endpoint_name: str
) -> List[Record]:
    """ASYNC Executes a read query using an injected async session and returns list of records."""
    if query is None:
        # Attempt to find the missing query name (optional improvement)
        missing_query_key = 'Unknown Query Key'
        for key, loaded_query in QUERIES.items():
            if loaded_query is None and key.lower() in endpoint_name.lower().replace(" ", ""):
                missing_query_key = key
                break
        print(f"ERROR ({endpoint_name}): Query template for '{missing_query_key}' not loaded.")
        raise HTTPException(status_code=500, detail=f"Internal server error: Query '{missing_query_key}' unavailable.")

    try:
        # MODIFIED: Define the transaction work function inside the try block
        async def transaction_work(tx: AsyncTransaction, cypher_query: str, query_params: dict):
            if cypher_query is None:
                # Attempt to find the missing query name (optional improvement)
                missing_query_key = 'Unknown Query Key'
                for key, loaded_query in QUERIES.items():
                    if loaded_query is None and key.lower() in endpoint_name.lower().replace(" ", ""):
                        missing_query_key = key
                        break
                print(f"ERROR ({endpoint_name}): Query template for '{missing_query_key}' is None.")
                raise ValueError(f"Query template for '{missing_query_key}' unavailable.")

            result: AsyncResult = await tx.run(cypher_query, query_params)
            records: List[Record] = [rec async for rec in result]
            summary = await result.consume()
            print(f"DEBUG ({endpoint_name}): Query executed, consumed {summary.counters.nodes_created} nodes, etc.")
            return records

        # MODIFIED: Use the passed-in session directly with execute_read
        records = await session.execute_read(
            lambda tx: transaction_work(tx, query, parameters)
        )

        print(f"DEBUG ({endpoint_name}): Retrieved {len(records)} records.")
        return records

    except neo4j_exceptions.Neo4jError as e:
        print(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error in {endpoint_name}: {e.code}")
    except ValueError as e: # Catch the ValueError raised for missing query
        print(f"ValueError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    except Exception as e:
        print(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error in {endpoint_name}")

# --- NEW Endpoint: GET / (Handles Listing & Filtering) ---
@router.get(
    "/",
    response_model=List[Concept],
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
    session: AsyncSession = Depends(get_db)
):
    """Handles fetching concepts with optional filters."""
    query = None
    parameters = {"limit": limit, "skip": skip}
    endpoint_name = "GetConcepts"

    if category_name:
        query = QUERIES.get('getConceptsByCategory')
        parameters["category"] = category_name
        endpoint_name += f"ByCategory:{category_name}"
    elif subcategory_name:
        query = QUERIES.get('getConceptsBySubcategory')
        parameters["subcategory"] = subcategory_name
        endpoint_name += f"BySubcategory:{subcategory_name}"
    elif confidence_threshold is not None: # Check for not None, as 0.0 is valid
        query = QUERIES.get('getConceptsByConfidence')
        parameters["threshold"] = confidence_threshold
        endpoint_name += f"ByConfidence>={confidence_threshold}"
    else:
        # Default query to get concepts without specific filters (needs 'getConcepts' query)
        query = QUERIES.get('getConcepts')
        endpoint_name += "(NoFilter)"
        # Ensure the 'getConcepts' query handles limit/skip

    if query is None:
        # This case is handled inside _execute_read_query_async now
        pass

    try:
        records = await _execute_read_query_async(session, query, parameters, endpoint_name)

        if not records:
            print(f"DEBUG ({endpoint_name}): No concepts found matching criteria.")
            return []

        # --- REVISED VALIDATION LOGIC ---
        validated_concepts = []
        for record in records:
            record_data = record.data()
            try:
                # Check if the default 'getConcepts' query returned the whole node
                if 'concept' in record_data and isinstance(record_data['concept'], dict):
                    # If query returned the whole node aliased as 'concept'
                    validated_concepts.append(Concept.model_validate(record_data['concept']))
                # Check if fields match expected return from confidence/category queries
                elif all(k in record_data for k in ['id', 'name', 'description', 'confidence']):
                     # Manually create a dict that matches the Concept model fields
                     # Note: Assumes 'confidence' from query maps to 'confidence_score' in model
                     concept_data_for_model = {
                         'id': record_data['id'],
                         'name': record_data['name'],
                         'description': record_data.get('description'), # Use .get for safety
                         'confidence_score': record_data['confidence'],
                         # Add default/None values for other required Concept fields if necessary
                         # e.g., 'quality': None, 'modality': None, ...
                     }
                     validated_concepts.append(Concept.model_validate(concept_data_for_model))
                else:
                    # Fallback or raise error if data format is unexpected
                    print(f"WARN ({endpoint_name}): Unexpected record data format: {record_data}")
                    # Option 1: Try validating the raw data anyway
                    # validated_concepts.append(Concept.model_validate(record_data))
                    # Option 2: Skip this record
                    continue

            except ValidationError as val_err:
                 # Log validation errors per record for better debugging
                 print(f"ERROR ({endpoint_name}): Pydantic validation failed for record: {record_data}. Error: {val_err}")
                 # Decide whether to skip the record or raise an overall 500
                 # continue # Option: skip invalid records

        # --- END REVISED VALIDATION LOGIC ---

        return validated_concepts

    except HTTPException as http_err:
        raise http_err # Re-raise known HTTP exceptions
    except Exception as e: # Catch other unexpected errors during processing/validation
        print(f"ERROR ({endpoint_name}): Unexpected error during concept processing: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error processing concepts in {endpoint_name}")

# --- REMOVE OLD Filtering Endpoints ---
# Remove get_concepts_by_confidence
# Remove get_concepts_by_category
# Remove get_concepts_by_subcategory (covered by GET /?subcategory_name=...)

# --- Routes MOVED from relationships.py ---
# Ensure paths start with /{concept_id}/...
# Update to use _execute_read_query_async helper

@router.get(
    "/{concept_id}/properties",
    response_model=List[Concept],
    summary="Get Properties of a Concept",
    description="Retrieves concepts that are properties (accidents) of a given concept (substance), linked via HAS_PROPERTY relationship.",
    tags=["Relationships"]
)
async def get_concept_properties(
    concept_id: str = Path(..., title="Concept ID"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Properties for '{concept_id}'"
    query = QUERIES.get('getConceptProperties')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    try:
        # Assuming the query returns the property concept node data directly, often as 'prop' or similar
        # Check your 'getConceptProperties' query's RETURN clause
        return [Concept.model_validate(record.data()['prop']) for record in records if 'prop' in record.data()]
    except ValidationError as e:
        print(f"ValidationError processing properties results for {concept_id}: {e}. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing properties results.")
    except KeyError as e:
        print(f"KeyError processing properties results for {concept_id}: {e}. Expected key not in record data. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing properties results (data format mismatch).")

@router.get(
    "/{concept_id}/causal-chain",
    response_model=List[PathResponse],
    summary="Get Causal Chain from a Concept",
    description="Retrieves causal chains (paths) starting from a given concept, up to a specified depth.",
    tags=["Relationships"]
)
async def get_causal_chain(
    concept_id: str = Path(..., title="Concept ID"),
    max_depth: int = Query(3, ge=1, le=5), result_limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "maxDepth": max_depth, "resultLimit": result_limit}
    endpoint_name = f"Causal Chain for '{concept_id}'"
    query = QUERIES.get('getCausalChain')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    paths = []
    try:
        for record in records:
            neo4j_path_obj = record.get("path") # Assumes query returns path alias 'path'
            if neo4j_path_obj:
                try:
                    paths.append(PathResponse.from_neo4j_path(neo4j_path_obj))
                except Exception as conversion_error:
                    print(f"Warning ({endpoint_name}): Failed to convert Neo4j Path object: {conversion_error} - Object: {neo4j_path_obj}")
            else:
                print(f"Warning ({endpoint_name}): Causal chain record did not contain a valid 'path' key: {record.data()}")
        # Return empty list if no paths found, consistent with GET /
        return paths
    except ValidationError as e: # If PathResponse validation fails
        print(f"ValidationError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail="Error processing path data")
    except Exception as e: # Catch other unexpected errors during processing
        print(f"Unexpected error processing paths in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error processing paths")

# --- Add other routes from relationships.py similarly ---
# get_all_relationships_for_concept -> "/{concept_id}/relationships"
# get_concept_hierarchy -> "/{concept_id}/hierarchy"
# get_concept_membership -> "/{concept_id}/membership"
# get_interacting_concepts -> "/{concept_id}/interacting"
# get_temporal_relationships -> "/{concept_id}/temporal"
# get_spatial_relationships -> "/{concept_id}/spatial"
# --- Make sure to use _execute_read_query_async and handle results/errors ---

# Example for get_all_relationships_for_concept:
@router.get(
    "/{concept_id}/relationships",
    response_model=List[RelationshipInfo],
    summary="Get All Relationships for a Concept",
    description="Retrieves all outgoing and incoming relationships for a given concept.",
    tags=["Relationships"]
)
async def get_all_relationships_for_concept(
    concept_id: str = Path(..., title="Concept ID"),
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "skip": skip, "limit": limit}
    endpoint_name = f"All Relationships for '{concept_id}'"
    query = QUERIES.get('getAllRelationshipsForConcept')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    try:
        # Assuming query returns data compatible with RelationshipInfo model directly
        return [RelationshipInfo.model_validate(record.data()) for record in records]
    except ValidationError as e:
        print(f"ValidationError processing all relationships results for {concept_id}: {e}. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing relationships results.")

# --- (Continue adding the rest of the relationship endpoints here) ---

@router.get(
    "/{concept_id}/hierarchy",
    response_model=List[PathResponse],
    summary="Get Concept Hierarchy (Containment)",
    description="Retrieves paths representing the containment hierarchy starting from a concept (using CONTAINS relationship).",
    tags=["Relationships"]
)
async def get_concept_hierarchy(
    concept_id: str = Path(..., title="Concept ID"),
    max_depth: int = Query(3, ge=1, le=5), result_limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "maxDepth": max_depth, "resultLimit": result_limit}
    endpoint_name = f"Hierarchy for '{concept_id}'"
    query = QUERIES.get('getConceptHierarchy')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    paths = []
    try:
        for record in records:
            neo4j_path_obj = record.get("path") # Assumes query returns path alias 'path'
            if neo4j_path_obj:
                try:
                    paths.append(PathResponse.from_neo4j_path(neo4j_path_obj))
                except Exception as conversion_error:
                    print(f"Warning ({endpoint_name}): Failed to convert Neo4j Path object: {conversion_error} - Object: {neo4j_path_obj}")
            else:
                print(f"Warning ({endpoint_name}): Hierarchy record did not contain a valid 'path' key: {record.data()}")
        return paths # Return empty list if no paths found
    except ValidationError as e:
        print(f"ValidationError processing hierarchy paths for {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing hierarchy path data")
    except Exception as e:
        print(f"Unexpected error processing hierarchy paths in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error processing hierarchy paths")


@router.get(
    "/{concept_id}/membership",
    response_model=List[PathResponse],
    summary="Get Concept Membership (Part Of)",
    description="Retrieves paths representing the membership hierarchy starting from a concept (using IS_PART_OF relationship).",
    tags=["Relationships"]
)
async def get_concept_membership(
    concept_id: str = Path(..., title="Concept ID"),
    max_depth: int = Query(3, ge=1, le=5), result_limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "maxDepth": max_depth, "resultLimit": result_limit}
    endpoint_name = f"Membership for '{concept_id}'"
    query = QUERIES.get('getConceptMembership')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    paths = []
    try:
        for record in records:
            neo4j_path_obj = record.get("path") # Assumes query returns path alias 'path'
            if neo4j_path_obj:
                try:
                    paths.append(PathResponse.from_neo4j_path(neo4j_path_obj))
                except Exception as conversion_error:
                    print(f"Warning ({endpoint_name}): Failed to convert Neo4j Path object: {conversion_error} - Object: {neo4j_path_obj}")
            else:
                print(f"Warning ({endpoint_name}): Membership record did not contain a valid 'path' key: {record.data()}")
        return paths # Return empty list if no paths found
    except ValidationError as e:
        print(f"ValidationError processing membership paths for {concept_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing membership path data")
    except Exception as e:
        print(f"Unexpected error processing membership paths in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error processing membership paths")


@router.get(
    "/{concept_id}/interacting",
    response_model=List[Concept],
    summary="Get Interacting Concepts (Community)",
    description="Retrieves concepts that interact with the given concept via the INTERACTS_WITH relationship.",
    tags=["Relationships"]
)
async def get_interacting_concepts(
    concept_id: str = Path(..., title="Concept ID"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Interacting Concepts for '{concept_id}'"
    query = QUERIES.get('getInteractingConcepts')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    try:
        # Assuming the query returns the 'other' concept node data directly, alias 'otherConcept' or similar
        # Check your 'getInteractingConcepts' query's RETURN clause
        return [Concept.model_validate(record.data()['otherConcept']) for record in records if 'otherConcept' in record.data()]
    except ValidationError as e:
        print(f"ValidationError processing interacting concepts for {concept_id}: {e}. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing interacting concepts.")
    except KeyError as e:
        print(f"KeyError processing interacting concepts for {concept_id}: {e}. Expected key not in record data. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing interacting concepts (data format mismatch).")


@router.get(
    "/{concept_id}/temporal",
    response_model=List[TemporalRelationshipInfo],
    summary="Get Temporal Relationships (Precedes)",
    description="Retrieves concepts that temporally precede or follow the given concept via the PRECEDES relationship.",
    tags=["Relationships"]
)
async def get_temporal_relationships(
    concept_id: str = Path(..., title="Concept ID"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Temporal Relationships for '{concept_id}'"
    query = QUERIES.get('getTemporalRelationships')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    try:
        # Assuming query returns data compatible with TemporalRelationshipInfo model directly
        return [TemporalRelationshipInfo.model_validate(record.data()) for record in records]
    except ValidationError as e:
        print(f"ValidationError processing temporal results for {concept_id}: {e}. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing temporal results.")


@router.get(
    "/{concept_id}/spatial",
    response_model=List[SpatialRelationshipInfo],
    summary="Get Spatial Relationships",
    description="Retrieves concepts spatially related to the given concept via the SPATIALLY_RELATES_TO relationship.",
    tags=["Relationships"]
)
async def get_spatial_relationships(
    concept_id: str = Path(..., title="Concept ID"),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    parameters = {"conceptId": concept_id, "limit": limit}
    endpoint_name = f"Spatial Relationships for '{concept_id}'"
    query = QUERIES.get('getSpatialRelationships')

    records = await _execute_read_query_async(session, query, parameters, endpoint_name)
    try:
        # Assuming query returns data compatible with SpatialRelationshipInfo model directly
        return [SpatialRelationshipInfo.model_validate(record.data()) for record in records]
    except ValidationError as e:
        print(f"ValidationError processing spatial results for {concept_id}: {e}. Records: {[r.data() for r in records]}")
        raise HTTPException(status_code=500, detail="Internal error processing spatial results.")

# --- End of Merged Routes ---

# --- ADD THE MISSING POST ENDPOINT ---
@router.post(
    "/",
    response_model=ConceptResponse, # Use your actual response model
    status_code=status.HTTP_201_CREATED, # Standard for successful creation
    summary="Create a New Concept",
    description="Creates a new concept node in the knowledge graph after validation.",
    tags=["Concepts"] # Add tag here if you want it grouped separately or keep it implicit
)
async def handle_create_concept(
    concept_in: ConceptCreate, # Input data model
    session: AsyncSession = Depends(get_db)
    # Add dependency injection for your service if applicable
    # concept_service: ConceptService = Depends(get_concept_service)
):
    """Handles the creation of a new concept."""
    try:
        # 1. Perform Kantian Validation (Pydantic validation already done)
        KantianValidator.validate_concept(concept_in.model_dump()) # Use model_dump()

        # 2. Call Service Layer or Direct DB Interaction
        # Example: Directly executing a CREATE query
        # NOTE: Ensure your CREATE query sets all required properties (id, name, timestamp, stability, confidence etc.)
        # You might need a dedicated 'createConcept' query template
        create_query = """
            CREATE (c:Concept {
                name: $name,
                description: $description,
                quality: $quality,
                modality: $modality,
                stability: $stability,
                confidence: $confidence,
                creation_timestamp: datetime(),
                id: randomUUID()
            })
            RETURN c { .*, id: c.id, elementId: elementId(c) } AS concept
        """
        parameters = concept_in.model_dump()
        # Add default values if not provided and required by DB
        parameters.setdefault('stability', 'ephemeral')
        parameters.setdefault('confidence', 0.5)
        parameters.setdefault('description', None)
        parameters.setdefault('quality', None)
        parameters.setdefault('modality', None)


        async def transaction_work(tx: AsyncTransaction, query: str, params: dict):
            result: AsyncResult = await tx.run(query, params)
            record: Optional[Record] = await result.single()
            summary = await result.consume()
            if record is None or summary.counters.nodes_created != 1:
                 raise RuntimeError("Concept creation failed in database.")
            # Ensure the returned data matches ConceptResponse structure
            # Neo4j driver returns dict directly if using RETURN c { ... }
            return record.data()['concept']

        created_concept_data = await session.execute_write(
            lambda tx: transaction_work(tx, create_query, parameters)
        )

        # Validate the data coming back from the DB against the response model
        return ConceptResponse.model_validate(created_concept_data)

    except KantianValidationError as exc:
        # Let the exception handler in main.py catch this
        raise exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Create Concept): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during concept creation: {db_err.code}")
    except ValidationError as pydantic_err: # Error validating DB result
         print(f"ERROR (Create Concept): Pydantic validation failed for DB result: {pydantic_err}")
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error processing created concept.")
    except Exception as e:
        print(f"ERROR (Create Concept): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during concept creation.")

# --- NEW Endpoint: Get Concept by Element ID ---
@router.get(
    "/{element_id}", # Use element_id as the path parameter
    response_model=ConceptResponse,
    summary="Get Concept by Element ID",
    description="Retrieves the details of a single concept using its Neo4j element ID.",
    tags=["Concepts"],
    responses={
        404: {"description": "Concept not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_concept_by_element_id(
    element_id: str = Path(..., title="Element ID", description="The Neo4j element ID of the concept to retrieve."),
    session: AsyncSession = Depends(get_db)
):
    """Handles fetching a single concept by its element ID."""
    # Define the query (consider loading from a file if preferred)
    # Ensure the RETURN projection matches the ConceptResponse model fields/aliases
    get_by_id_query = """
        MATCH (c:Concept)
        WHERE elementId(c) = $element_id
        RETURN c {
            .*,                 // Include all node properties
            id: c.id,          // Explicitly include custom ID if needed
            elementId: elementId(c) // Always include elementId
            // Ensure 'confidence' property is included for the model alias
        } AS concept
        LIMIT 1
    """
    parameters = {"element_id": element_id}
    endpoint_name = f"GetConceptByID:{element_id}"

    try:
        async def transaction_work(tx: AsyncTransaction, query: str, params: dict):
            result: AsyncResult = await tx.run(query, params)
            # Use strict=False as we want to handle None explicitly for 404
            record: Optional[Record] = await result.single(strict=False)
            # No need to consume here if we only expect one record or None
            return record.data() if record else None # Return data dict or None

        # Using execute_read as we are just reading
        concept_data = await session.execute_read(
            lambda tx: transaction_work(tx, get_by_id_query, parameters)
        )

        if concept_data is None:
            print(f"INFO ({endpoint_name}): Concept not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

        # Data should be in {'concept': {details}} structure due to RETURN alias
        if 'concept' not in concept_data:
             print(f"ERROR ({endpoint_name}): Query did not return expected 'concept' key. Data: {concept_data}")
             raise HTTPException(status_code=500, detail="Internal server error processing concept data.")

        # Validate the data against the response model
        validated_concept = ConceptResponse.model_validate(concept_data['concept'])
        return validated_concept

    except neo4j_exceptions.Neo4jError as e:
        print(f"Neo4jError in {endpoint_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error in {endpoint_name}: {e.code}")
    except ValidationError as val_err: # Error validating DB result
         print(f"ERROR ({endpoint_name}): Pydantic validation failed for DB result: {val_err}")
         raise HTTPException(status_code=500, detail="Internal server error processing retrieved concept.")
    except HTTPException as http_err:
        raise http_err # Re-raise known HTTP exceptions (like the 404)
    except Exception as e:
        print(f"Unexpected error in {endpoint_name}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error in {endpoint_name}")

@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_concept_by_element_id(
    element_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Deletes a concept node by its element ID.
    Uses DETACH DELETE to remove the node and any relationships connected to it.
    Returns 204 No Content on successful deletion.
    Returns 404 Not Found if the concept does not exist.
    """
    query = """
    MATCH (c)
    WHERE elementId(c) = $element_id
    DETACH DELETE c
    RETURN count(c) AS deleted_count
    """
    try:
        result = await session.run(query, {"element_id": element_id})
        record = await result.single()

        if not record or record["deleted_count"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept with element ID '{element_id}' not found.",
            )
        # Success case (implicit return None -> 204)

    except HTTPException as http_exc:
        # Re-raise HTTPException directly so FastAPI handles it
        raise http_exc
    except Exception as e:
        # Catch *other*, truly unexpected exceptions
        # logger.error(f"Error deleting concept {element_id}: {e}", exc_info=True) # Proper logging
        print(f"!!! UNEXPECTED Error deleting concept {element_id}: {type(e).__name__} - {e}") # (Can remove/refine later)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred while trying to delete concept {element_id}.",
        )

@router.patch("/{element_id}", response_model=ConceptResponse)
async def update_concept_partial(
    element_id: str,
    concept_update: ConceptUpdate,
    session: AsyncSession = Depends(get_db),
):
    """
    Partially updates a concept node by its element ID.
    Only updates the fields provided in the request body.
    Returns the updated concept data.
    Returns 404 Not Found if the concept does not exist.
    """
    # Get only the fields that were actually sent in the request
    update_data = concept_update.model_dump(exclude_unset=True)

    # Check if there's anything to update
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided.",
        )

    # Cypher query to find the node, update it, and return it
    query = """
    MATCH (c:Concept)
    WHERE elementId(c) = $element_id
    SET c += $update_data
    RETURN c, elementId(c) AS elementId
    """

    try:
        result = await session.run(
            query, {"element_id": element_id, "update_data": update_data}
        )
        record = await result.single()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept with element ID '{element_id}' not found.",
            )

        # Process the returned record into the response model
        updated_node_data = record["c"]
        returned_element_id = record["elementId"]
        response_data = {**updated_node_data, "elementId": returned_element_id}

        # Return the updated concept, validated by the response model
        return ConceptResponse(**response_data)

    except HTTPException as http_exc:
        # Re-raise HTTPException directly
        raise http_exc
    except Exception as e:
        # Log unexpected errors
        # logger.error(f"Error updating concept {element_id}: {e}", exc_info=True)
        print(f"!!! UNEXPECTED Error updating concept {element_id}: {type(e).__name__} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred while trying to update concept {element_id}.",
        )