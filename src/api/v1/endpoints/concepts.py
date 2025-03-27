from fastapi import APIRouter, Depends, HTTPException, Query, Path
from neo4j import Driver, Result, exceptions as neo4j_exceptions
from typing import List

from src.db.neo4j_driver import get_driver
from src.models.concept import Concept
# Import the query loader utility
from src.utils.cypher_loader import load_query

router = APIRouter()

# --- Load Queries ---
try:
    GET_CONCEPTS_BY_CATEGORY_QUERY = load_query('getConceptsByCategory')
    GET_CONCEPTS_BY_SUBCATEGORY_QUERY = load_query('getConceptsBySubcategory') # Load the new query
except (FileNotFoundError, KeyError) as e:
    print(f"FATAL ERROR: Could not load required query: {e}")
    # Handle error during startup - setting to None allows checks later
    if 'GET_CONCEPTS_BY_CATEGORY_QUERY' not in locals():
        GET_CONCEPTS_BY_CATEGORY_QUERY = None
    if 'GET_CONCEPTS_BY_SUBCATEGORY_QUERY' not in locals():
        GET_CONCEPTS_BY_SUBCATEGORY_QUERY = None


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


# --- NEW ENDPOINT ---
@router.get(
    "/concepts/subcategory/{subcategory_name}",
    response_model=List[Concept],
    summary="Get Concepts by Subcategory Name",
    description="Retrieves a paginated list of concepts belonging directly to a specific Kantian subcategory (e.g., Causality, Unity)."
)
async def get_concepts_by_subcategory(
    subcategory_name: str = Path(
        ..., # Required path parameter
        title="Name of the Subcategory",
        description="The specific Kantian subcategory name (case-sensitive).",
        # Add some examples for documentation
        examples=["Causality", "Unity", "Reality", "Possibility/Impossibility"]
    ),
    skip: int = Query(0, ge=0, title="Skip", description="Number of concepts to skip."),
    limit: int = Query(10, ge=1, le=100, title="Limit", description="Max concepts to return."),
    driver: Driver = Depends(get_driver)
):
    """Handles the request to fetch concepts based on their subcategory."""
    if GET_CONCEPTS_BY_SUBCATEGORY_QUERY is None:
         raise HTTPException(status_code=500, detail="Internal server error: Query template 'getConceptsBySubcategory' not loaded.")

    # Note: The parameter name in the query template is 'subcategory'
    parameters = {
        "subcategory": subcategory_name, # Match the parameter name in the Cypher query
        "skip": skip,
        "limit": limit
    }
    try:
        result: Result = driver.execute_query(
            GET_CONCEPTS_BY_SUBCATEGORY_QUERY, # Use the loaded query string
            parameters_=parameters,
            database_="neo4j"
        )
        concepts_data = [record.data() for record in result.records]
        concepts = [Concept.model_validate(record) for record in concepts_data]
        return concepts
    except neo4j_exceptions.Neo4jError as db_error:
        # Log the database error details
        print(f"Database error querying concepts for subcategory '{subcategory_name}': {db_error}")
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail=f"Database error retrieving concepts for subcategory '{subcategory_name}'."
        )
    except Exception as e:
        # Log the general exception details
        print(f"Unexpected error querying concepts for subcategory '{subcategory_name}': {e}")
        raise HTTPException(
            status_code=500, # Internal Server Error
            detail=f"Unexpected error retrieving concepts for subcategory '{subcategory_name}'."
        )