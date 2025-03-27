from fastapi import APIRouter, Depends, HTTPException, Query, Path
from neo4j import Driver, Result, exceptions as neo4j_exceptions
from typing import List

# Correctly import the driver and the model from their respective modules
from src.db.neo4j_driver import get_driver
from src.models.concept import Concept

router = APIRouter()

# Define the query template logic here
# This query finds concepts linked to a specific category via subcategories
GET_CONCEPTS_BY_CATEGORY_QUERY = """
MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category {name: $category_name})
RETURN
    c.id AS id,
    c.name AS name,
    c.description AS description,
    c.confidence_score AS confidence_score // Ensure DB field name is returned
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

@router.get(
    "/concepts/category/{category_name}",
    response_model=List[Concept], # Expect a list of Concept objects
    summary="Get Concepts by Category Name",
    description="Retrieves a paginated list of concepts belonging to a specific Kantian category (e.g., Relation, Quality). Concepts are matched via their subcategory relationship."
)
async def get_concepts_by_category(
    # Path parameter validation
    category_name: str = Path(
        ..., # Ellipsis means this path parameter is required
        title="Name of the Category",
        description="The specific Kantian category name (case-sensitive).",
        examples=["Relation", "Quality", "Quantity", "Modality"]
    ),
    # Query parameter validation for pagination
    skip: int = Query(
        0,
        ge=0, # Must be greater than or equal to 0
        title="Skip",
        description="Number of concepts to skip for pagination."
    ),
    limit: int = Query(
        10,
        ge=1, # Must be greater than or equal to 1
        le=100, # Limit maximum to 100 for performance
        title="Limit",
        description="Maximum number of concepts to return."
    ),
    # Dependency injection to get the Neo4j driver
    driver: Driver = Depends(get_driver)
):
    """
    Handles the request to fetch concepts based on their category.
    """
    parameters = {
        "category_name": category_name,
        "skip": skip,
        "limit": limit
    }
    try:
        # Execute the query using the driver's recommended method
        result: Result = driver.execute_query(
            GET_CONCEPTS_BY_CATEGORY_QUERY,
            parameters_=parameters,
            database_="neo4j" # Specify the database name if not default
        )

        # Process the results into dictionaries
        concepts_data = [record.data() for record in result.records]

        # Check if any concepts were found (optional, returning empty list is fine)
        if not concepts_data:
             pass # Just return the empty list generated below

        # Validate and convert data using the Pydantic model
        # This automatically handles the alias mapping for 'confidence_score'
        concepts = [Concept.model_validate(record) for record in concepts_data]

        return concepts

    # Handle potential database errors
    except neo4j_exceptions.Neo4jError as db_error:
        # Log the database error details (important for debugging)
        print(f"Database error querying concepts for category '{category_name}': {db_error}")
        raise HTTPException(
            status_code=503, # Service Unavailable might be appropriate
            detail=f"Database error while retrieving concepts for category '{category_name}'. Please try again later."
        )
    # Handle any other unexpected errors
    except Exception as e:
        # Log the general exception details
        print(f"Unexpected error querying concepts for category '{category_name}': {e}")
        raise HTTPException(
            status_code=500, # Internal Server Error
            detail=f"An unexpected error occurred while retrieving concepts for category '{category_name}'."
        )
