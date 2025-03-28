import pytest
import pytest_asyncio
from httpx import AsyncClient
import collections # For comparing lists

# Expected categories based on category_structure_statements.py (adjust if needed)
EXPECTED_MAIN_CATEGORIES = sorted(["Quantity", "Quality", "Relation", "Modality"])

@pytest.mark.asyncio
async def test_get_all_categories(async_client: AsyncClient):
    """
    Tests retrieving the list of main category names.
    """
    print("\nTesting GET /api/v1/categories")
    response = await async_client.get("/api/v1/categories")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"

    try:
        categories = response.json()
        if not isinstance(categories, list):
            pytest.fail(f"Expected response to be a list, but got {type(categories)}. Response: {response.text}")

        # Ensure all items are strings
        assert all(isinstance(cat, str) for cat in categories), f"Expected list of strings, but got: {categories}"

        print(f"Found categories: {sorted(categories)}")

        # Compare content regardless of order
        assert collections.Counter(categories) == collections.Counter(EXPECTED_MAIN_CATEGORIES), \
            f"Mismatch in categories. Expected: {EXPECTED_MAIN_CATEGORIES}. Found: {sorted(categories)}"

    except Exception as e:
        pytest.fail(f"Failed to parse JSON response or validate categories. Error: {e}. Response: {response.text}")

# Add more tests here if category endpoints expand (e.g., getting subcategories) 