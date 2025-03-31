from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
from neo4j import AsyncSession, exceptions as neo4j_exceptions, AsyncTransaction
import traceback

from src.db.neo4j_driver import get_db
from src.models.category import (
    CategoryListResponse,
    CategoryResponse,
    SubCategoryResponse,
    CategoryCreate,
    SubCategoryCreate,
    CategoryUpdate
)
# Import the query constants
from src.cypher_queries.category_queries import (
    LIST_CATEGORIES, GET_CATEGORY_BY_NAME, CREATE_CATEGORY,
    CHECK_PARENT_CATEGORY, CREATE_SUBCATEGORY
)

router = APIRouter()

@router.get(
    "/",
    response_model=CategoryListResponse,
    summary="List All Categories and Subcategories",
    description="Retrieve a list of all top-level categories, including their associated subcategories.",
    tags=["Categories"]
)
async def list_categories(
    tx: Annotated[AsyncTransaction, Depends(get_db)]
) -> CategoryListResponse:
    """Retrieve all categories and their subcategories from the database."""
    categories_list: List[CategoryResponse] = []
    try:
        result = await tx.run(LIST_CATEGORIES)
        records = await result.data() # Fetch all records

        for record in records:
            # Filter out None values from subcategory data list
            filtered_sub_data = [sub for sub in record['subcategories_data'] if sub is not None]
            
            # Create SubCategoryResponse objects
            sub_responses = [SubCategoryResponse.model_validate(sub_data) for sub_data in filtered_sub_data]

            # Create CategoryResponse object
            category_response = CategoryResponse(
                elementId=record['cat_elementId'],
                name=record['cat_name'],
                description=record['cat_description'],
                subcategories=sub_responses
            )
            categories_list.append(category_response)

        return CategoryListResponse(categories=categories_list)

    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        # Basic error logging, consider using a proper logger
        print(f"ERROR (List Categories): Database error - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error listing categories: {db_err.code}")
    except Exception as e:
        print(f"ERROR (List Categories): Unexpected error - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while listing categories.")

@router.get(
    "/{name}",
    response_model=CategoryResponse,
    summary="Get Category or Subcategory by Name",
    description=(
        "Retrieve the details of a specific category by its name. "
        "If the provided name matches a subcategory, the details of its parent category (including all its subcategories) will be returned."
    ),
    tags=["Categories"]
)
async def get_category_by_name(
    name: str,
    tx: Annotated[AsyncTransaction, Depends(get_db)]
) -> CategoryResponse:
    """Retrieve category details by name, resolving subcategory names to their parent category."""
    try:
        result = await tx.run(GET_CATEGORY_BY_NAME, {"name": name})
        record = await result.single() # Fetch the single record

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category or Subcategory with name '{name}' not found."
            )

        # Process the record data
        filtered_sub_data = [sub for sub in record['subcategories_data'] if sub is not None]
        sub_responses = [SubCategoryResponse.model_validate(sub_data) for sub_data in filtered_sub_data]

        # Validate and return the CategoryResponse
        return CategoryResponse(
            elementId=record['cat_elementId'],
            name=record['cat_name'],
            description=record['cat_description'],
            subcategories=sub_responses
        )

    except HTTPException as http_exc: # Re-raise 404
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Get Category by Name): Database error for name '{name}' - {db_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error retrieving category: {db_err.code}")
    except Exception as e:
        print(f"ERROR (Get Category by Name): Unexpected error for name '{name}' - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while retrieving the category.") 

@router.post(
    "/",
    response_model=CategoryResponse, # Return the full CategoryResponse
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Top-Level Category",
    description="Create a new top-level category node.",
    tags=["Categories"],
)
async def create_category(
    category_data: CategoryCreate,
    tx: Annotated[AsyncTransaction, Depends(get_db)],
) -> CategoryResponse:
    """Create a new top-level category."""
    try:
        result = await tx.run(
            CREATE_CATEGORY,
            {"name": category_data.name, "description": category_data.description},
        )
        record = await result.single()

        if record is None: # Should not happen with CREATE if successful
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create category node in the database."
             )

        # Return a CategoryResponse, subcategories will be empty
        return CategoryResponse(
            elementId=record["elementId"],
            name=record["name"],
            description=record["description"],
            subcategories=[]
        )

    except neo4j_exceptions.ConstraintError as constraint_err:
        # Specific handling for uniqueness constraint violation
        print(f"ERROR (Create Category): Constraint error for name '{category_data.name}' - {constraint_err}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with the name '{category_data.name}' already exists.",
        )
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Create Category): Database error for name '{category_data.name}' - {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating category: {db_err.code}",
        )
    except Exception as e:
        print(f"ERROR (Create Category): Unexpected error for name '{category_data.name}' - {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the category.",
        )


@router.post(
    "/{parent_category_name}/subcategories",
    response_model=SubCategoryResponse, # Return just the created SubCategory
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Subcategory",
    description="Create a new subcategory under a specified parent category.",
    tags=["Categories"],
)
async def create_subcategory(
    parent_category_name: str,
    subcategory_data: SubCategoryCreate,
    tx: Annotated[AsyncTransaction, Depends(get_db)],
) -> SubCategoryResponse:
    """Create a new subcategory and link it to a parent category."""
    try:
        # Check if parent exists first *within the same transaction*
        parent_result = await tx.run(CHECK_PARENT_CATEGORY, {"parent_name": parent_category_name})
        if await parent_result.single() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category '{parent_category_name}' not found.",
            )

        # If parent exists, proceed to create subcategory
        result = await tx.run(
            CREATE_SUBCATEGORY,
            {
                "parent_name": parent_category_name,
                "sub_name": subcategory_data.name,
                "sub_description": subcategory_data.description,
            },
        )
        record = await result.single()

        if record is None:
             # If parent exists but record is still None, creation failed unexpectedly
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subcategory node or relationship after parent check."
             )

        # Validate and return the SubCategoryResponse
        return SubCategoryResponse.model_validate(record)

    except neo4j_exceptions.ConstraintError as constraint_err:
        # Specific handling for uniqueness constraint violation
        print(f"ERROR (Create Subcategory): Constraint error for name '{subcategory_data.name}' - {constraint_err}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A subcategory with the name '{subcategory_data.name}' already exists.",
        )
    except HTTPException as http_exc: # Re-raise 404
        raise http_exc
    except (neo4j_exceptions.Neo4jError, neo4j_exceptions.DriverError) as db_err:
        print(f"ERROR (Create Subcategory): Database error for subcategory '{subcategory_data.name}' under '{parent_category_name}' - {db_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating subcategory: {db_err.code}",
        )
    except Exception as e:
        print(f"ERROR (Create Subcategory): Unexpected error for subcategory '{subcategory_data.name}' under '{parent_category_name}' - {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the subcategory.",
        )