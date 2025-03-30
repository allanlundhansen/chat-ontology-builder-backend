# tests/integration/test_category_endpoints.py
import pytest
from httpx import AsyncClient
from fastapi import status

# Define the base endpoint path
CATEGORIES_ENDPOINT = "/api/v1/categories/"

# Expected Categories and some Subcategories (based on sample data)
EXPECTED_CATEGORIES = ["Quantity", "Quality", "Relation", "Modality"]
EXPECTED_SUBCATEGORIES = {
    "Quantity": ["Unity", "Plurality", "Totality"],
    "Quality": ["Reality", "Negation", "Limitation"],
    "Relation": ["Substance", "Causality", "Community"],
    "Modality": ["Possibility/Impossibility", "Existence/Non-existence", "Necessity/Contingency"],
}

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data") # Ensure categories are loaded
async def test_list_categories_success(async_client: AsyncClient):
    """Test successfully retrieving the list of all categories and their subcategories."""
    # Act
    response = await async_client.get(CATEGORIES_ENDPOINT)

    # Assert Status Code
    assert response.status_code == status.HTTP_200_OK

    # Assert Response Structure
    data = response.json()
    assert isinstance(data, dict)
    assert "categories" in data
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) == len(EXPECTED_CATEGORIES)

    # Assert Content
    found_categories = set()
    for category in data["categories"]:
        assert "elementId" in category
        assert "name" in category
        assert "description" in category # Even if None
        assert "subcategories" in category
        assert isinstance(category["subcategories"], list)
        
        found_categories.add(category["name"])
        assert category["name"] in EXPECTED_CATEGORIES
        assert len(category["subcategories"]) == len(EXPECTED_SUBCATEGORIES.get(category["name"], []))

        found_sub_names = set()
        for subcategory in category["subcategories"]:
            assert "elementId" in subcategory
            assert "name" in subcategory
            assert "description" in subcategory
            found_sub_names.add(subcategory["name"])
        
        assert found_sub_names == set(EXPECTED_SUBCATEGORIES.get(category["name"], []))

    assert found_categories == set(EXPECTED_CATEGORIES)

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data")
async def test_get_category_by_name_success(async_client: AsyncClient):
    """Test successfully retrieving a specific category by its name."""
    category_name = "Relation"
    expected_subs = EXPECTED_SUBCATEGORIES[category_name]

    # Act
    response = await async_client.get(f"{CATEGORIES_ENDPOINT}{category_name}")

    # Assert Status Code
    assert response.status_code == status.HTTP_200_OK

    # Assert Response Structure and Content
    category = response.json()
    assert isinstance(category, dict)
    assert category["name"] == category_name
    assert "elementId" in category
    assert "description" in category
    assert "subcategories" in category
    assert isinstance(category["subcategories"], list)
    assert len(category["subcategories"]) == len(expected_subs)

    found_sub_names = {sub["name"] for sub in category["subcategories"]}
    assert found_sub_names == set(expected_subs)
    for sub in category["subcategories"]:
        assert "elementId" in sub
        assert "description" in sub

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data")
async def test_get_category_by_subcategory_name_success(async_client: AsyncClient):
    """Test retrieving category details by providing a subcategory name."""
    subcategory_name = "Causality" # Belongs to Relation
    expected_parent_category_name = "Relation"
    expected_parent_subs = EXPECTED_SUBCATEGORIES[expected_parent_category_name]

    # Act
    response = await async_client.get(f"{CATEGORIES_ENDPOINT}{subcategory_name}")

    # Assert Status Code
    assert response.status_code == status.HTTP_200_OK

    # Assert Response Structure and Content (should be the PARENT category)
    category = response.json()
    assert isinstance(category, dict)
    assert category["name"] == expected_parent_category_name
    assert "elementId" in category
    assert "description" in category
    assert "subcategories" in category
    assert isinstance(category["subcategories"], list)
    assert len(category["subcategories"]) == len(expected_parent_subs)

    found_sub_names = {sub["name"] for sub in category["subcategories"]}
    assert found_sub_names == set(expected_parent_subs)
    assert subcategory_name in found_sub_names # Ensure the queried subcategory is present

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data")
async def test_get_category_not_found(async_client: AsyncClient):
    """Test attempting to retrieve a category/subcategory that does not exist."""
    non_existent_name = "DoesNotExist"

    # Act
    response = await async_client.get(f"{CATEGORIES_ENDPOINT}{non_existent_name}")

    # Assert Status Code
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- Tests for POST Endpoints ---

@pytest.mark.anyio
async def test_create_category_success(async_client: AsyncClient):
    """Test successfully creating a new top-level category."""
    category_name = "Test Create Category"
    category_desc = "A category created during testing."
    payload = {"name": category_name, "description": category_desc}

    # Act
    response = await async_client.post(CATEGORIES_ENDPOINT, json=payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_201_CREATED

    # Assert Response Structure and Content
    data = response.json()
    assert isinstance(data, dict)
    assert "elementId" in data
    assert data["name"] == category_name
    assert data["description"] == category_desc
    assert "subcategories" in data
    assert isinstance(data["subcategories"], list)
    assert len(data["subcategories"]) == 0 # New categories have no subs

    # Optional: Verify with a GET request
    get_response = await async_client.get(f"{CATEGORIES_ENDPOINT}{category_name}")
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json()["name"] == category_name


@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data") # Need parent category 'Relation'
async def test_create_subcategory_success(async_client: AsyncClient):
    """Test successfully creating a new subcategory under an existing parent."""
    parent_category_name = "Relation"
    subcategory_name = "Test Create SubCategory"
    subcategory_desc = "A subcategory created during testing."
    payload = {"name": subcategory_name, "description": subcategory_desc}
    url = f"{CATEGORIES_ENDPOINT}{parent_category_name}/subcategories"

    # Act
    response = await async_client.post(url, json=payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_201_CREATED

    # Assert Response Structure and Content (should be SubCategoryResponse)
    data = response.json()
    assert isinstance(data, dict)
    assert "elementId" in data
    assert data["name"] == subcategory_name
    assert data["description"] == subcategory_desc

    # Optional: Verify parent category now lists the new subcategory
    get_response = await async_client.get(f"{CATEGORIES_ENDPOINT}{parent_category_name}")
    assert get_response.status_code == status.HTTP_200_OK
    parent_data = get_response.json()
    found = False
    for sub in parent_data["subcategories"]:
        if sub["name"] == subcategory_name:
            found = True
            break
    assert found, f"Subcategory '{subcategory_name}' not found under parent '{parent_category_name}' after creation."


@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data") # Need existing category 'Quantity'
async def test_create_category_conflict(async_client: AsyncClient):
    """Test creating a category with a name that already exists."""
    existing_category_name = "Quantity" # From sample data
    payload = {"name": existing_category_name, "description": "Attempting conflict"}

    # Act
    response = await async_client.post(CATEGORIES_ENDPOINT, json=payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data") # Need existing sub 'Unity' under 'Quantity'
async def test_create_subcategory_conflict(async_client: AsyncClient):
    """Test creating a subcategory with a name that already exists."""
    parent_category_name = "Quantity"
    existing_subcategory_name = "Unity" # From sample data
    payload = {"name": existing_subcategory_name, "description": "Attempting conflict"}
    url = f"{CATEGORIES_ENDPOINT}{parent_category_name}/subcategories"

    # Act
    response = await async_client.post(url, json=payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.anyio
async def test_create_subcategory_parent_not_found(async_client: AsyncClient):
    """Test creating a subcategory under a non-existent parent category."""
    parent_category_name = "DoesNotExist"
    subcategory_name = "Test SubCategory Orphan"
    payload = {"name": subcategory_name, "description": "Should fail"}
    url = f"{CATEGORIES_ENDPOINT}{parent_category_name}/subcategories"

    # Act
    response = await async_client.post(url, json=payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
async def test_create_category_missing_name(async_client: AsyncClient):
    """Test creating a category with missing required 'name' field."""
    payload = {"description": "Missing name"} # Name is required

    # Act
    response = await async_client.post(CATEGORIES_ENDPOINT, json=payload)

    # Assert Status Code (FastAPI/Pydantic validation)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 