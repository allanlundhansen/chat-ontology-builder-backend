# src/models/category.py
from pydantic import BaseModel, Field
from typing import Optional, List

class SubCategoryResponse(BaseModel):
    elementId: str = Field(..., description="Unique element ID assigned by the database.")
    name: str = Field(..., description="Unique name of the subcategory.")
    description: Optional[str] = Field(None, description="Optional description of the subcategory.")
    # Add other fields if needed, e.g., number of concepts linked?

class CategoryResponse(BaseModel):
    elementId: str = Field(..., description="Unique element ID assigned by the database.")
    name: str = Field(..., description="Unique name of the category.")
    description: Optional[str] = Field(None, description="Optional description of the category.")
    subcategories: List[SubCategoryResponse] = Field(default_factory=list, description="List of subcategories belonging to this category.")

class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse] = Field(..., description="A list of all top-level categories, potentially including their subcategories.")

# --- New Models for CRUD ---

class CategoryCreate(BaseModel):
    name: str = Field(..., description="Unique name for the new category.", examples=["New Category"])
    description: Optional[str] = Field(None, description="Optional description for the new category.", examples=["A description of the new category."])

class SubCategoryCreate(BaseModel):
    name: str = Field(..., description="Unique name for the new subcategory.", examples=["New SubCategory"])
    description: Optional[str] = Field(None, description="Optional description for the new subcategory.", examples=["A description of the new subcategory."])
    # parent_category_name will likely be a path parameter in the endpoint

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Optional new name for the category or subcategory.", examples=["Updated Name"])
    description: Optional[str] = Field(None, description="Optional new description for the category or subcategory.", examples=["An updated description."])
    # We might need more complex logic if renaming needs to check for conflicts,
    # or if changing descriptions needs specific handling. 