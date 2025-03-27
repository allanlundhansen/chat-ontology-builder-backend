from fastapi import APIRouter, Depends, HTTPException, Query, Path
# Remove 'Path as Neo4jPath' from this import
from neo4j import Driver, Result, exceptions as neo4j_exceptions
from typing import List

from src.db.neo4j_driver import get_driver
from src.models.concept import Concept
# Import the new Path model
from src.models.path import PathResponse
from src.utils.cypher_loader import load_query

router = APIRouter()

# --- Load Queries ---
# Attempt to load queries at module level for efficiency
# Handle potential errors during loading
try:
    GET_CONCEPTS_BY_CATEGORY_QUERY = load_query('getConceptsByCategory')
except (FileNotFoundError, KeyError) as e_cat:
    print(f"ERROR loading 'getConceptsByCategory': {e_cat}")
    GET_CONCEPTS_BY_CATEGORY_QUERY = None

try:
    GET_CONCEPTS_BY_SUBCATEGORY_QUERY = load_query('getConceptsBySubcategory')
except (FileNotFoundError, KeyError) as e_subcat:
    print(f"ERROR loading 'getConceptsBySubcategory': {e_subcat}")
    GET_CONCEPTS_BY_SUBCATEGORY_QUERY = None

# --- Load NEW Queries ---
try:
    GET_CONCEPT_PROPERTIES_QUERY = load_query('getConceptProperties')
except (FileNotFoundError, KeyError) as e_props:
    print(f"ERROR loading 'getConceptProperties': {e_props}")
    GET_CONCEPT_PROPERTIES_QUERY = None

try:
    GET_CAUSAL_CHAIN_QUERY = load_query('getCausalChain')
except (FileNotFoundError, KeyError) as e_causal:
    print(f"ERROR loading 'getCausalChain': {e_causal}")
    GET_CAUSAL_CHAIN_QUERY = None


# --- Existing Endpoints ---
@router.get(
    "/concepts/category/{category_name}",
    response_model=List[Concept],
    summary="Get Concepts by Category Name",
    description="Retrieves a paginated list of concepts belonging to a specific Kantian category (e.g., Relation, Quality). Concepts are matched via their subcategory relationship."
)
async def get_concepts_by_category(
    category_name: str = Path(
        ...,
        title="Name of the Category",
        description="The specific Kantian category name (case-sensitive).",
        examples=["Relation", "Quality", "Quantity", "Modality"]
    ),
    skip: int = Query(0, ge=0, title="Skip", description="Number of concepts to skip."),
    limit: int = Query(10, ge=1, le=100, title="Limit", description="Max concepts to return."),
    driver: Driver = Depends(get_driver)
):
    """Handles the request to fetch concepts based on their category."""
    if GET_CONCEPTS_BY_CATEGORY_QUERY is None:
         raise HTTPException(status_code=500, detail="Internal server error: Query template 'getConceptsByCategory' not loaded.")

    # Parameter name in query template is 'category'
    parameters = {"category": category_name, "skip": skip, "limit": limit}
    try:
        result: Result = driver.execute_query(
            GET_CONCEPTS_BY_CATEGORY_QUERY, parameters_=parameters, database_="neo4j"
        )
        concepts_data = [record.data() for record in result.records]
        concepts = [Concept.model_validate(record) for record in concepts_data]
        return concepts
    except neo4j_exceptions.Neo4jError as db_error:
        print(f"Database error querying concepts for category '{category_name}': {db_error}")
        raise HTTPException(status_code=503, detail=f"Database error retrieving concepts for category '{category_name}'.")
    except Exception as e:
        print(f"Unexpected error querying concepts for category '{category_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error retrieving concepts for category '{category_name}'.")


@router.get(
    "/concepts/subcategory/{subcategory_name}",
    response_model=List[Concept],
    summary="Get Concepts by Subcategory Name",
    description="Retrieves a paginated list of concepts belonging directly to a specific Kantian subcategory (e.g., Causality, Unity)."
)
async def get_concepts_by_subcategory(
    subcategory_name: str = Path(
        ...,
        title="Name of the Subcategory",
        description="The specific Kantian subcategory name (case-sensitive).",
        examples=["Causality", "Unity", "Reality", "Possibility/Impossibility"]
    ),
    skip: int = Query(0, ge=0, title="Skip", description="Number of concepts to skip."),
    limit: int = Query(10, ge=1, le=100, title="Limit", description="Max concepts to return."),
    driver: Driver = Depends(get_driver)
):
    """Handles the request to fetch concepts based on their subcategory."""
    if GET_CONCEPTS_BY_SUBCATEGORY_QUERY is None:
         raise HTTPException(status_code=500, detail="Internal server error: Query template 'getConceptsBySubcategory' not loaded.")

    # Parameter name in query template is 'subcategory'
    parameters = {"subcategory": subcategory_name, "skip": skip, "limit": limit}
    try:
        result: Result = driver.execute_query(
            GET_CONCEPTS_BY_SUBCATEGORY_QUERY, parameters_=parameters, database_="neo4j"
        )
        concepts_data = [record.data() for record in result.records]
        concepts = [Concept.model_validate(record) for record in concepts_data]
        return concepts
    except neo4j_exceptions.Neo4jError as db_error:
        print(f"Database error querying concepts for subcategory '{subcategory_name}': {db_error}")
        raise HTTPException(status_code=503, detail=f"Database error retrieving concepts for subcategory '{subcategory_name}'.")
    except Exception as e:
        print(f"Unexpected error querying concepts for subcategory '{subcategory_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error retrieving concepts for subcategory '{subcategory_name}'.")


# --- NEW ENDPOINT: Get Concept Properties ---
@router.get(
    "/concepts/{concept_id}/properties",
    response_model=List[Concept], # Properties are also concepts
    summary="Get Properties of a Concept",
    description="Retrieves concepts that are properties (accidents) of a given concept (substance), linked via HAS_PROPERTY relationship."
)
async def get_concept_properties(
    concept_id: str = Path(..., title="Concept ID", description="The unique ID of the concept (substance)."),
    limit: int = Query(50, ge=1, le=100, title="Limit", description="Maximum number of properties to return."),
    driver: Driver = Depends(get_driver)
):
    """Handles the request to fetch properties of a concept."""
    if GET_CONCEPT_PROPERTIES_QUERY is None:
         raise HTTPException(status_code=500, detail="Internal server error: Query template 'getConceptProperties' not loaded.")

    # Parameter name in query template is 'conceptId'
    parameters = {"conceptId": concept_id, "limit": limit}
    try:
        result: Result = driver.execute_query(
            GET_CONCEPT_PROPERTIES_QUERY, parameters_=parameters, database_="neo4j"
        )
        # The query returns id, name, description, confidence of the property concepts
        concepts_data = [record.data() for record in result.records]
        concepts = [Concept.model_validate(record) for record in concepts_data]
        return concepts
    except neo4j_exceptions.Neo4jError as db_error:
        print(f"Database error querying properties for concept '{concept_id}': {db_error}")
        raise HTTPException(status_code=503, detail=f"Database error retrieving properties for concept '{concept_id}'.")
    except Exception as e:
        print(f"Unexpected error querying properties for concept '{concept_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error retrieving properties for concept '{concept_id}'.")


# --- MODIFIED ENDPOINT: Get Causal Chain ---
@router.get(
    "/concepts/{concept_id}/causal-chain",
    response_model=List[PathResponse],
    summary="Get Causal Chain from a Concept",
    description="Retrieves causal chains (paths) starting from a given concept, up to a specified depth."
)
async def get_causal_chain(
    concept_id: str = Path(..., title="Concept ID", description="The unique ID of the starting concept."),
    max_depth: int = Query(3, ge=1, le=5, title="Max Depth", description="Maximum length of the causal chain path."),
    result_limit: int = Query(10, ge=1, le=50, title="Result Limit", description="Maximum number of paths to return."),
    driver: Driver = Depends(get_driver)
):
    """Handles the request to fetch causal chains starting from a concept."""
    if GET_CAUSAL_CHAIN_QUERY is None:
         raise HTTPException(status_code=500, detail="Internal server error: Query template 'getCausalChain' not loaded.")

    # Parameter names in query template are 'conceptId', 'maxDepth', 'resultLimit'
    parameters = {
        "conceptId": concept_id,
        "maxDepth": max_depth,
        "resultLimit": result_limit
    }
    try:
        result: Result = driver.execute_query(
            GET_CAUSAL_CHAIN_QUERY, parameters_=parameters, database_="neo4j"
        )
        paths = []
        for record in result.records:
            # Get the path object from the record
            neo4j_path_obj = record.get("path")
            # Check if a path object was actually returned
            if neo4j_path_obj:
                try:
                    # Attempt conversion using the class method
                    paths.append(PathResponse.from_neo4j_path(neo4j_path_obj))
                except Exception as conversion_error:
                    # Log if conversion fails for some reason
                    print(f"Warning: Failed to convert Neo4j Path object: {conversion_error} - Object: {neo4j_path_obj}")
            else:
                # Log a warning if the path is missing
                print(f"Warning: Record did not contain a 'path' key: {record.data()}")

        return paths
    except neo4j_exceptions.Neo4jError as db_error:
        print(f"Database error querying causal chain for concept '{concept_id}': {db_error}")
        raise HTTPException(status_code=503, detail=f"Database error retrieving causal chain for concept '{concept_id}'.")
    except Exception as e:
        print(f"Unexpected error querying causal chain for concept '{concept_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error retrieving causal chain for concept '{concept_id}'.")