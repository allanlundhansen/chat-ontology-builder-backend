from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver, Result
from typing import List

from src.db.neo4j_driver import get_driver

router = APIRouter()

# Define a simple response model (though for just names, a list is fine)
# class Category(BaseModel):
#     name: str

@router.get("/categories", response_model=List[str])
async def get_all_categories(driver: Driver = Depends(get_driver)):
    """
    Retrieves a list of all main Kantian category names.
    """
    query = "MATCH (c:Category) RETURN c.name AS name ORDER BY name"
    try:
        # Use execute_query for managed transactions (recommended)
        result: Result = driver.execute_query(query)
        # Extract the 'name' from each record
        categories = [record["name"] for record in result.records]
        return categories
    except Exception as e:
        # Log the exception details here in a real application
        print(f"Error querying categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories from database.") 