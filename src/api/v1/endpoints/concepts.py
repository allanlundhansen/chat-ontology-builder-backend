from fastapi import APIRouter, Depends, HTTPException, Query, Path
from neo4j import Driver, Result
from typing import List

from src.db.neo4j_driver import get_driver
from src.models.concept import Concept # Import the model

router = APIRouter()

# Define the query template logic here (or load from file later)
GET_CONCEPTS_BY_CATEGORY_QUERY = """
MATCH (c:Concept)-[:INSTANCE_OF]->(sub:Subcategory)<-[:HAS_SUBCATEGORY]-(cat:Category {name: $category_name})
RETURN c.id AS id, c.name AS name, c.description AS description, c.confidence_score AS confidence
ORDER BY c.name
SKIP $skip
LIMIT $limit
"""

@router.get(
    "/concepts/category/{category_name}",
    response_model=List[Concept],
    summary="Get Concepts by Category Name"
)
async def get_concepts_by_category(
    category_name: str = Path(..., title="Name of the Category", description="The specific Kantian category (e.g., Relation, Quality)."),
    skip: int = Query(0, ge=0, title="Skip", description="Number of concepts to skip for pagination."),
    limit: int = Query(10, ge=1, le=100, title="Limit", description="Maximum number of concepts to return."),
    driver: Driver = Depends(get_driver)
):
    """
    Retrieves a paginated list of concepts belonging to a specific Kantian category.
    Concepts are matched via their subcategory relationship.
    """
    parameters = {
        "category_name": category_name,
        "skip": skip,
        "limit": limit
    }
    try:
        result: Result = driver.execute_query(
            GET_CONCEPTS_BY_CATEGORY_QUERY,
            parameters_=parameters,
            database_="neo4j" # Specify database if needed, often default
        )
        # Convert records to Concept model instances
        # Note: result.records gives a list of Record objects
        # record.data() gives a dictionary view of the record
        concepts = [Concept(**record.data()) for record in result.records]
        return concepts
    except Exception as e:
        # Log the exception details here in a real application
        print(f"Error querying concepts for category '{category_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve concepts for category '{category_name}'.")
