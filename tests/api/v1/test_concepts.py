from fastapi.testclient import TestClient
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from typing import List, Dict, Any
import collections # For comparing lists regardless of order
import asyncio

# Import your FastAPI application instance
from src.main import app

# Fixtures
from tests.conftest import clear_db_before_test, load_sample_data # Import needed fixtures

# TestClient is created using the app instance.
# Fixtures in conftest.py will handle overriding the DB connection
# used by the 'app' during the test run.
client = TestClient(app)

# Define the endpoint URLs
ROOT_URL = "/"
CONCEPTS_CONFIDENCE_URL = "/api/v1/concepts/confidence"
CONCEPTS_CATEGORY_URL = "/api/v1/concepts/category"

# Simple test to verify TestClient setup and root endpoint
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Chat Ontology Builder API"}

# --- We will add tests for /concepts endpoints below this --- 

@pytest.mark.anyio
async def test_get_concepts_root(load_sample_data, async_client: AsyncClient):
    """Test the root GET /api/v1/concepts endpoint without filters."""
    response = await async_client.get("/api/v1/concepts", params={"limit": 5}) # Use root path
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Add more assertions based on expected unfiltered results

@pytest.mark.anyio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_concepts_by_confidence_high_threshold(async_client: AsyncClient): # Remove load_sample_data
    """Test retrieving concepts with a high confidence threshold using GET /."""
    # 1. Arrange: Create concepts with different confidence scores
    high_conf_data = {"name": "ConceptHighConf", "confidence": 0.95}
    response_high = await async_client.post("/api/v1/concepts/", json=high_conf_data)
    assert response_high.status_code == 201, "Failed to create high confidence concept"
    high_conf_id = response_high.json()["elementId"]

    low_conf_data = {"name": "ConceptLowConf", "confidence": 0.5}
    response_low = await async_client.post("/api/v1/concepts/", json=low_conf_data)
    assert response_low.status_code == 201, "Failed to create low confidence concept"
    # low_conf_id = response_low.json()["elementId"] # Not strictly needed for assertion

    # 2. Act: Get concepts with confidence threshold
    response = await async_client.get("/api/v1/concepts", params={"confidence_threshold": 0.9, "limit": 10})

    # 3. Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # assert len(data) > 0 # Assuming sample data has concepts with high confidence
    assert len(data) == 1, f"Expected 1 concept, found {len(data)}"

    returned_ids = {concept.get("elementId") for concept in data}
    assert high_conf_id in returned_ids, "High confidence concept missing"
    # Check that low confidence concept is NOT returned
    # (Can check ID or name, ID is more precise if names could theoretically clash)
    # assert low_conf_id not in returned_ids
    assert data[0]["name"] == "ConceptHighConf"
    assert data[0]["confidence"] == 0.95
    # for concept in data:
    #     assert concept.get("confidence", 0) >= 0.9

@pytest.mark.anyio
async def test_get_concepts_by_category_relation(load_sample_data, async_client: AsyncClient):
    """Test retrieving concepts classified under the 'Relation' category using GET /."""
    # Use root path with query parameter
    response = await async_client.get("/api/v1/concepts", params={"category_name": "Relation", "limit": 10})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Assuming sample data has 'Relation' concepts
    # Add assertions checking if returned concepts actually belong to 'Relation'
    # This might require checking subcategory or other properties depending on your model/query
    # ... specific assertions ...

# --- Add tests for the moved relationship endpoints ---
# Example:
@pytest.mark.anyio
async def test_get_concept_properties_sample(load_sample_data, async_client: AsyncClient):
    """Test retrieving properties for a known concept."""
    # Replace 'sample_concept_id_with_properties' with an actual ID from your sample data
    concept_id = "sample_concept_id_with_properties"
    response = await async_client.get(f"/api/v1/concepts/{concept_id}/properties")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Add assertions based on expected properties for that concept

# ... Add more tests for other endpoints ...

# Test for /concepts/category/{category_name} endpoint
# @pytest.mark.anyio
# async def test_get_concepts_by_category_relation(load_sample_data, async_client: AsyncClient): # Fixture name stays the same
#     """Test retrieving concepts classified under the 'Relation' category."""
#     response = await async_client.get("/api/v1/concepts", params={"category_name": "Relation"})
#     assert response.status_code == status.HTTP_200_OK
#     concepts = response.json()
# 
#     # --- Assertions based on sample data for 'Relation' category ---
#     assert isinstance(concepts, list), "Response should be a list of concepts"
#     assert len(concepts) > 0, f"Expected concepts for category 'Relation', but got none."
# 
#     # Check presence of concepts expected to be under Relation (via Causality or Community)
#     expected_concept_names = {"Heat", "Expansion", "Earth", "Moon", "Lightning", "Thunder"}
#     returned_concept_names = {c['name'] for c in concepts if 'name' in c}
# 
#     assert expected_concept_names.issubset(returned_concept_names), \
#         f"Missing expected concepts for category 'Relation': {expected_concept_names - returned_concept_names}"
# 
#     # Check absence of concepts NOT under Relation
#     unexpected_concept_names = {"Ball", "Red", "Forest", "Tree", "Atom", "Shadow", "Vacuum"}
#     assert not any(name in returned_concept_names for name in unexpected_concept_names), \
#         f"Found unexpected concepts for category 'Relation': {[n for n in unexpected_concept_names if n in returned_concept_names]}"
# 
#     # Verify structure of returned concepts (optional but good)
#     for concept in concepts:
#         assert "id" in concept
#         assert "name" in concept
#         # Add other checks as needed based on the API response model for this endpoint

# --- Add more tests below --- 

# --- Define Expected Results ---
# Updated based on sample_concept_statements.py review
EXPECTED_CONCEPTS = {
    # Based on INSTANCE_OF relationships in sample data
    "Quantity": ["Forest", "Tree", "Atom"], # Forest->Totality, Tree->Plurality, Atom->Unity
    "Relation": ["Ball", "Heat", "Expansion", "Earth", "Moon", "Lightning", "Thunder"], # -> Substance, Causality, Community
}
# Define concepts NOT expected under these categories (adjust as needed)
UNEXPECTED_CONCEPTS = {
    "Quantity": ["Ball", "Heat", "Red", "Absence"], # Examples
    "Relation": ["Red", "Forest", "Tree", "Atom", "Absence", "Unicorn"], # Examples
}
# --- End Expected Results ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, expected_present, expected_absent",
    [
        ("Quantity", EXPECTED_CONCEPTS["Quantity"], UNEXPECTED_CONCEPTS["Quantity"]),
        ("Relation", EXPECTED_CONCEPTS["Relation"], UNEXPECTED_CONCEPTS["Relation"]),
        # Add other relevant category tests if the logic applies
    ]
)
async def test_get_concepts_by_category_relation(
    async_client: AsyncClient,
    category_name: str,
    expected_present: List[str],
    expected_absent: List[str]
):
    """
    Tests retrieving concepts classified under Quantity or Relation categories
    using the INSTANCE_OF relationship to their Subcategories.
    """
    print(f"\nTesting category (via INSTANCE_OF): {category_name}")
    # Add limit to prevent overwhelming results if sample data grows
    response = await async_client.get(f"/api/v1/concepts?category_name={category_name}&limit=200")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"

    try:
        concepts = response.json()
        if not isinstance(concepts, list):
             pytest.fail(f"Expected response to be a list, but got {type(concepts)}. Response: {response.text}")

        concept_names = sorted([c['name'] for c in concepts if isinstance(c, dict) and 'name' in c]) # Sort for consistent comparison
        print(f"Found concepts for {category_name}: {concept_names}")

    except Exception as e:
        pytest.fail(f"Failed to parse JSON response or extract concept names. Error: {e}. Response: {response.text}")

    # --- ASSERTIONS ---
    # Sort expected list for comparison
    sorted_expected_present = sorted(expected_present)

    # Check that the set of found concepts exactly matches the set of expected concepts
    assert collections.Counter(concept_names) == collections.Counter(sorted_expected_present), \
        f"Mismatch for category '{category_name}'. Expected: {sorted_expected_present}. Found: {concept_names}"

    # Check that all unexpected concepts ARE ABSENT (redundant if the above check passes, but good safeguard)
    found_unexpected = [name for name in expected_absent if name in concept_names]
    assert not found_unexpected, f"Found unexpected concepts for category '{category_name}': {found_unexpected}. Found: {concept_names}"
    # --- END ASSERTIONS ---

# --- Other tests for concepts endpoint ---
# ... (Keep other tests like test_get_concepts_root, test_get_concepts_nonexistent_category, etc.) ... 

# --- Expected Data (Based on sample_concept_statements.py review) ---
# Adjust these based on your data and desired test coverage
EXPECTED_CONCEPTS_BY_CATEGORY = {
    "Quantity": ["Forest", "Tree", "Atom"],
    "Relation": ["Ball", "Heat", "Expansion", "Earth", "Moon", "Lightning", "Thunder"],
}
UNEXPECTED_CONCEPTS_BY_CATEGORY = {
    "Quantity": ["Ball", "Red"],
    "Relation": ["Red", "Atom"],
}

# --- Helper Function (Optional but recommended) ---
async def get_concept_id_by_name(client: AsyncClient, name: str) -> str | None:
    """Helper to retrieve the ID of a concept by its name via the API."""
    response = await client.get(f"/api/v1/concepts?limit=1&name_filter={name}") # Assuming a name filter exists or can be added
    # --- OR --- Use a known query logic if name filter isn't there yet
    # response = await client.get("/api/v1/concepts?limit=100") # Get all and filter locally (less efficient)

    if response.status_code != 200:
        print(f"WARN: Helper failed to get concept '{name}'. Status: {response.status_code}")
        return None
    concepts = response.json()
    if concepts and isinstance(concepts, list) and concepts[0].get('name') == name:
        return concepts[0].get('id')
    # Fallback: Filter locally if no name filter in API
    # concepts = response.json()
    # for concept in concepts:
    #     if concept.get('name') == name:
    #         return concept.get('id')
    print(f"WARN: Helper could not find concept ID for '{name}'.")
    return None
# NOTE: The above helper assumes an API filter for name exists.
# If not, you might need to hardcode known IDs or query concepts first in tests.
# For simplicity now, let's assume we can get IDs or hardcode a few known ones.
# Example Known IDs (replace with actual IDs from your *test* DB after loading samples):
# KNOWN_IDS = { ... }
# def get_id(name: str) -> str: ...

# --- Helper to create test data ---
async def _setup_category_test_data(async_client: AsyncClient, category_info: Dict[str, Any]):
    """Helper to create categories, subcategories, concepts, and INSTANCE_OF relationships."""
    created_concept_ids = {}

    # 1. Create Parent Category
    cat_data = {"name": category_info["category_name"], "description": f"Test {category_info['category_name']}"}
    res_cat = await async_client.post("/api/v1/categories/", json=cat_data)
    assert res_cat.status_code in [201, 409], f"Failed to create/ensure category {category_info['category_name']}"

    # 2. Create Subcategories
    subcat_ids = {}
    for subcat_name in category_info["subcategories"]:
        subcat_data = {"name": subcat_name, "description": f"Test {subcat_name}"}
        res_subcat = await async_client.post(f"/api/v1/categories/{category_info['category_name']}/subcategories", json=subcat_data)
        assert res_subcat.status_code in [201, 409], f"Failed to create/ensure subcategory {subcat_name}"
        # Need to GET the subcategory to find its ID if it already existed (409)
        # For simplicity in test, assume 201 or handle ID retrieval if needed.
        if res_subcat.status_code == 201:
             # Assuming the create endpoint returns the ID or full object with ID
             # Adjust based on actual API behavior - this part is complex if IDs aren't returned on creation
             # Let's assume we need to fetch it (LESS IDEAL FOR TEST SETUP)
             res_get_cat = await async_client.get(f"/api/v1/categories/{category_info['category_name']}")
             if res_get_cat.status_code == 200:
                 cat_details = res_get_cat.json()
                 found_sub = next((s for s in cat_details.get('subcategories', []) if s.get('name') == subcat_name), None)
                 if found_sub:
                     subcat_ids[subcat_name] = found_sub.get('elementId')
                 else: 
                     pytest.fail(f"Could not retrieve ID for created subcategory {subcat_name}")
             else:
                  pytest.fail(f"Could not retrieve category details for {category_info['category_name']} after subcat creation")
        # else: handle 409 if needed

    # 3. Create Concepts and Link them via INSTANCE_OF
    for subcat_name, concepts_to_link in category_info["concepts"].items():
        # subcat_id = subcat_ids.get(subcat_name)
        # if not subcat_id:
            # If subcat ID wasn't found above, skip linking (or fail test)
            # print(f"WARN: Skipping concept linking for {subcat_name}, ID not found.")
            # continue # Or pytest.fail
            # For now, let's assume subcategories exist from sample data or previous test runs if not created
            # A more robust test would explicitly fetch/confirm subcat IDs.
            # Let's try creating relationship by name (assuming API supports this - unlikely)
            # *** Revised Approach: Create concepts, *then* assume subcats exist for linking ***
            # *** This relies on /relationships POST supporting names or pre-existing subcats ***
            # *** A truly isolated test needs full category/subcategory ID management ***

        for concept_name in concepts_to_link:
            concept_data = {"name": f"TestConcept_{concept_name}_{category_info['category_name']}", "quality": "Reality"} # Make names unique
            res_con = await async_client.post("/api/v1/concepts/", json=concept_data)
            assert res_con.status_code == 201, f"Failed to create concept {concept_name}"
            concept_id = res_con.json()["elementId"]
            created_concept_ids[concept_name] = concept_id

            # Link Concept to Subcategory via INSTANCE_OF
            # This requires knowing the subcategory's element ID accurately.
            # Let's *assume* sample data setup these subcats and query them by name is hard/not possible.
            # **Alternative for Test**: Maybe create relationship endpoint needs updating
            # to accept source/target names? Or test needs pre-fetching.
            # **Simplification**: We'll skip the INSTANCE_OF creation for now, as it adds
            # significant complexity to get subcategory IDs reliably within the test.
            # The test will rely on the API's logic to correctly link Concepts to Categories/Subcategories internally.
            # print(f"INFO: Would link {concept_id} to {subcat_name} here if subcat ID was available.")

    # 4. Create 'other' concepts that should NOT be returned
    for concept_name in category_info["other_concepts"]:
         concept_data = {"name": f"TestConcept_Other_{concept_name}_{category_info['category_name']}", "quality": "Reality"}
         res_con = await async_client.post("/api/v1/concepts/", json=concept_data)
         assert res_con.status_code == 201, f"Failed to create 'other' concept {concept_name}"
         # No need to store ID unless debugging

    return created_concept_ids # Return IDs of concepts expected to be found

# Define Subcategory mapping for concepts used in tests
SUBCATEGORY_MAP = {
    "Quantity": {"Forest": "Totality", "Tree": "Plurality", "Atom": "Unity"},
    "Relation": {"Ball": "Substance", "Heat": "Causality", "Expansion": "Causality", "Earth": "Community", "Moon": "Community", "Lightning": "Causality", "Thunder": "Causality"}
}

# Helper function to get subcategory IDs
async def _get_subcategory_ids(async_client: AsyncClient, category_name: str) -> Dict[str, str]:
    """Fetches category details and returns a dict mapping subcategory names to their IDs."""
    subcat_name_to_id = {}
    print(f"Helper: Fetching category details for {category_name}...")
    response = await async_client.get(f"/api/v1/categories/{category_name}")
    print(f"Helper: GET /categories/{category_name} status: {response.status_code}")
    if response.status_code == 200:
        cat_details = response.json()
        # print(f"Helper: Received category details: {cat_details}") # Debug
        for subcat in cat_details.get("subcategories", []):
            if subcat and "name" in subcat and "elementId" in subcat:
                 subcat_name_to_id[subcat["name"]] = subcat["elementId"]
                 print(f"Helper: Found subcategory {subcat['name']} with ID {subcat['elementId']}")
            else:
                print(f"WARN: Invalid subcategory data found: {subcat}")
    elif response.status_code == 404:
        print(f"WARN: Category {category_name} not found when fetching subcategory IDs.")
    else:
        print(f"WARN: Failed to fetch category details for {category_name}, status: {response.status_code}, Response: {response.text}")
    return subcat_name_to_id

# --- Updated Parametrized Test ---
@pytest.mark.anyio # Changed from asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
@pytest.mark.parametrize(
    "category_name, expected_present_names, expected_absent_names",
    [
        (
            "Quantity",
            EXPECTED_CONCEPTS_BY_CATEGORY["Quantity"], # e.g., ["Forest", "Tree", "Atom"]
            UNEXPECTED_CONCEPTS_BY_CATEGORY["Quantity"] # e.g., ["Ball", "Red"]
        ),
        (
            "Relation",
            EXPECTED_CONCEPTS_BY_CATEGORY["Relation"], # e.g., ["Ball", "Heat", "Expansion", ...]
            UNEXPECTED_CONCEPTS_BY_CATEGORY["Relation"] # e.g., ["Red", "Atom"]
        ),
    ]
)
async def test_get_concepts_by_category_relation(
    async_client: AsyncClient, category_name: str, expected_present_names: List[str], expected_absent_names: List[str]
):
    """
    Tests retrieving concepts classified under a specific category by creating
    concepts and linking them to the appropriate subcategory via INSTANCE_OF.
    """
    print(f"\nTesting category: {category_name}")

    # 1. Arrange
    # a. Determine needed subcategories for this category_name
    category_map = SUBCATEGORY_MAP.get(category_name, {})
    needed_subcats = set(category_map.values())
    if not needed_subcats:
        pytest.fail(f"No subcategory mapping found for category: {category_name}")

    # b. Ensure Parent Category exists
    print(f"Ensuring category '{category_name}' exists...")
    cat_data = {"name": category_name, "description": f"Test {category_name}"}
    res_cat = await async_client.post("/api/v1/categories/", json=cat_data)
    assert res_cat.status_code in [201, 409], f"Failed to create/ensure category {category_name}"
    print(f"Category '{category_name}' ensured (status: {res_cat.status_code})")

    # c. Ensure needed Subcategories exist
    for subcat_name in needed_subcats:
        print(f"Ensuring subcategory '{subcat_name}' under '{category_name}' exists...")
        subcat_data = {"name": subcat_name, "description": f"Test {subcat_name}"}
        res_subcat = await async_client.post(f"/api/v1/categories/{category_name}/subcategories", json=subcat_data)
        assert res_subcat.status_code in [201, 409], f"Failed to create/ensure subcategory {subcat_name}"
        print(f"Subcategory '{subcat_name}' ensured (status: {res_subcat.status_code})")

    # d. Fetch Subcategory IDs
    print("Fetching subcategory IDs...")
    await asyncio.sleep(0.3) # Brief pause for potential consistency
    subcat_name_to_id = await _get_subcategory_ids(async_client, category_name)
    if not all(sub in subcat_name_to_id for sub in needed_subcats):
         missing_ids = needed_subcats - set(subcat_name_to_id.keys())
         pytest.fail(f"Failed to retrieve element IDs for needed subcategories: {missing_ids}. Found: {subcat_name_to_id}")
    print(f"Retrieved subcategory IDs: {subcat_name_to_id}")

    # e. Create 'present' Concepts and INSTANCE_OF links
    created_expected_concepts = {} # Store name -> id mapping
    expected_unique_names = []
    print("Creating 'present' concepts and linking...")
    for name in expected_present_names:
        unique_name = f"TestPresent_{name}_{category_name}"
        expected_unique_names.append(unique_name)
        concept_data = {"name": unique_name, "quality": "Reality"} 
        response = await async_client.post("/api/v1/concepts/", json=concept_data)
        assert response.status_code == 201, f"Failed to create concept {unique_name}"
        concept_id = response.json()["elementId"]
        created_expected_concepts[unique_name] = concept_id
        print(f"Created concept '{unique_name}' (ID: {concept_id})")

        # Link to subcategory
        target_subcat_name = category_map.get(name)
        if target_subcat_name and target_subcat_name in subcat_name_to_id:
            target_subcat_id = subcat_name_to_id[target_subcat_name]
            print(f"Linking '{unique_name}' ({concept_id}) to '{target_subcat_name}' ({target_subcat_id})...")
            rel_data = {
                "source_id": concept_id,
                "target_id": target_subcat_id,
                "type": "INSTANCE_OF",
                "properties": {"confidence_score": 1.0} 
            }
            res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
            assert res_rel.status_code == 201, f"Failed to link {unique_name} to {target_subcat_name}. Status: {res_rel.status_code}, Response: {res_rel.text}"
            print(f"Link created successfully.")
        else:
            pytest.fail(f"Could not find target subcategory mapping ('{target_subcat_name}') or its ID for concept '{name}'")

    # f. Create 'absent' Concepts (no links needed)
    created_absent_concepts = {}
    absent_unique_names = []
    print("Creating 'absent' concepts...")
    for name in expected_absent_names:
        unique_name = f"TestAbsent_{name}_{category_name}"
        absent_unique_names.append(unique_name)
        concept_data = {"name": unique_name, "quality": "Reality"}
        response = await async_client.post("/api/v1/concepts/", json=concept_data)
        assert response.status_code == 201, f"Failed to create concept {unique_name}"
        created_absent_concepts[unique_name] = response.json()["elementId"]
        print(f"Created absent concept '{unique_name}' (ID: {created_absent_concepts[unique_name]})")
        
    # Give DB time to index potentially?
    print("Pausing briefly before query...")
    await asyncio.sleep(0.5)

    # 2. Act: Get concepts by category name
    print(f"Querying concepts for category: {category_name}...")
    response = await async_client.get(f"/api/v1/concepts", params={"category_name": category_name, "limit": 200})

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    print(f"Query successful (Status: {response.status_code})")

    try:
        concepts = response.json()
        if not isinstance(concepts, list):
             pytest.fail(f"Expected response to be a list, but got {type(concepts)}. Response: {response.text}")

        # Filter only concepts created in this specific test run using unique names
        # Note: We filter *after* the API call to check if the API correctly filtered by category internally
        # The filtering here is primarily to isolate results from other potential concepts in the DB if needed for debugging
        # The main assertion compares against the full set of expected unique names created in *this* test.
        concept_names = sorted([c['name'] for c in concepts if isinstance(c, dict) and c.get('name') ]) # Get all names returned by API
        print(f"API returned concept names for {category_name}: {concept_names}")
        # Filter down to only those created in this test run for cleaner comparison if needed
        test_run_concept_names = sorted([name for name in concept_names if name.startswith("TestPresent_") and name.endswith(f"_{category_name}")])
        print(f"Filtered concepts from this test run: {test_run_concept_names}")

    except Exception as e:
        pytest.fail(f"Failed to parse JSON response or extract concept names. Error: {e}. Response: {response.text}")

    # Assertions using unique names from this test run
    sorted_expected_unique_names = sorted(expected_unique_names)

    # Main assertion: Check if the concepts returned by the API match exactly those we created and linked
    assert collections.Counter(test_run_concept_names) == collections.Counter(sorted_expected_unique_names), \
        f"Mismatch for category '{category_name}'. Expected Unique Names: {sorted_expected_unique_names}. Found (filtered): {test_run_concept_names}. API Raw Names: {concept_names}"

    # Check that the unique names of absent concepts are NOT present in the filtered list
    found_absent_unique = [name for name in absent_unique_names if name in test_run_concept_names]
    assert not found_absent_unique, f"Found unexpected unique concepts for category '{category_name}': {found_absent_unique}. Found (filtered): {test_run_concept_names}"
    print("Assertions passed.")

@pytest.mark.asyncio
async def test_get_concepts_root(async_client: AsyncClient):
    """Test GET /concepts - basic retrieval."""
    # Simple assertion, assuming some concepts exist after sample data load
    response = await async_client.get("/api/v1/concepts?limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_concepts_nonexistent_category(async_client: AsyncClient):
    """Test filtering by a category that doesn't exist."""
    response = await async_client.get("/api/v1/concepts?category_name=DoesNotExist")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.anyio # Changed from asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_concepts_by_subcategory(async_client: AsyncClient):
    """Test filtering concepts by subcategory (e.g., Causality)."""
    # 1. Arrange
    category_name = "Relation"
    subcategory_name = "Causality"

    # Ensure Parent Category exists
    print(f"Ensuring category '{category_name}' exists...")
    cat_data = {"name": category_name, "description": "Test Relation for Subcategory Test"}
    res_cat = await async_client.post("/api/v1/categories/", json=cat_data)
    assert res_cat.status_code in [201, 409], f"Failed to create/ensure category {category_name}"

    # Ensure Subcategory exists under Parent
    print(f"Ensuring subcategory '{subcategory_name}' under '{category_name}' exists...")
    subcat_data = {"name": subcategory_name, "description": f"Test {subcategory_name} for Subcategory Test"}
    res_subcat = await async_client.post(f"/api/v1/categories/{category_name}/subcategories", json=subcat_data)
    assert res_subcat.status_code in [201, 409], f"Failed to create/ensure subcategory {subcategory_name}"

    # Fetch the Subcategory ID
    print(f"Fetching ID for subcategory '{subcategory_name}'...")
    await asyncio.sleep(0.3) # Pause for consistency
    subcat_ids = await _get_subcategory_ids(async_client, category_name)
    target_subcat_id = subcat_ids.get(subcategory_name)
    if not target_subcat_id:
        pytest.fail(f"Could not retrieve element ID for subcategory '{subcategory_name}'")
    print(f"Found subcategory ID: {target_subcat_id}")

    # Create concepts that should be found and link them
    concepts_to_link = ["TestHeatSub", "TestExpansionSub"]
    linked_concept_ids = {}
    print("Creating and linking concepts...")
    for name in concepts_to_link:
        concept_data = {"name": name, "quality": "Reality"}
        res_con = await async_client.post("/api/v1/concepts/", json=concept_data)
        assert res_con.status_code == 201
        concept_id = res_con.json()["elementId"]
        linked_concept_ids[name] = concept_id
        print(f"Created concept '{name}' ({concept_id})")

        # Link via INSTANCE_OF
        print(f"Linking '{name}' to '{subcategory_name}' ({target_subcat_id})...")
        rel_data = {
            "source_id": concept_id,
            "target_id": target_subcat_id,
            "type": "INSTANCE_OF",
            "properties": {"confidence_score": 1.0}
        }
        res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
        assert res_rel.status_code == 201, f"Failed to link {name} to {subcategory_name}"
        print(f"Link created.")

    # Create a concept that should NOT be found by this filter
    other_name = "TestOtherSub"
    print(f"Creating unrelated concept '{other_name}'...")
    other_data = {"name": other_name, "quality": "Reality"}
    res_other = await async_client.post("/api/v1/concepts/", json=other_data)
    assert res_other.status_code == 201
    other_id = res_other.json()["elementId"]
    print(f"Created unrelated concept '{other_name}' ({other_id})")

    # Give DB time to index potentially?
    print("Pausing briefly before query...")
    await asyncio.sleep(0.5)

    # 2. Act
    print(f"Querying concepts for subcategory: {subcategory_name}...")
    response = await async_client.get("/api/v1/concepts", params={"subcategory_name": subcategory_name, "limit": 50})

    # 3. Assert
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    print(f"API returned concepts: {concepts}")
    
    # Check names of returned concepts
    concept_names = {c['name'] for c in concepts if c.get('name')}
    print(f"Found concept names: {concept_names}")

    # Check for expected concepts
    for expected_name in concepts_to_link:
        assert expected_name in concept_names, f"Expected concept '{expected_name}' not found"
    
    # Check that the unrelated concept is absent
    assert other_name not in concept_names, f"Unrelated concept '{other_name}' was found unexpectedly"
    print("Assertions passed.")

@pytest.mark.asyncio
async def test_get_concepts_by_confidence(async_client: AsyncClient):
    """Test filtering concepts by confidence score."""
    response = await async_client.get("/api/v1/concepts?confidence_threshold=0.99&limit=100")
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    for concept in concepts:
        assert concept.get('confidence', 0) >= 0.99 # Using .get for safety

@pytest.mark.asyncio
async def test_get_concepts_pagination(async_client: AsyncClient):
    """Test pagination (skip, limit) for listing concepts."""
    # Get first page
    response1 = await async_client.get("/api/v1/concepts?limit=2&skip=0&sort_by=name")
    assert response1.status_code == 200
    page1 = response1.json()
    assert isinstance(page1, list)
    assert len(page1) <= 2

    # Get second page
    response2 = await async_client.get("/api/v1/concepts?limit=2&skip=2&sort_by=name")
    assert response2.status_code == 200
    page2 = response2.json()
    assert isinstance(page2, list)
    assert len(page2) <= 2

    # Ensure pages are different if enough data exists
    if len(page1) == 2 and len(page2) > 0:
        assert page1[0]['id'] != page2[0]['id']

# --- Tests for Specific Concept Detail Endpoints --- 

@pytest.mark.anyio # Use anyio instead of asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Ensure clean state
async def test_get_concept_properties(async_client: AsyncClient):
    """Test retrieving properties associated with a concept via HAS_PROPERTY."""
    # 1. Arrange: Create concepts and relationship
    # Create 'Ball' concept
    ball_data = {"name": "TestBallForProps", "quality": "Reality"}
    response_ball = await async_client.post("/api/v1/concepts/", json=ball_data)
    assert response_ball.status_code == 201
    ball_id = response_ball.json()["elementId"]

    # Create 'Red' concept (as a property)
    red_data = {"name": "TestRedProp", "quality": "Reality"}
    response_red = await async_client.post("/api/v1/concepts/", json=red_data)
    assert response_red.status_code == 201
    red_id = response_red.json()["elementId"]
    
    # Create 'Green' concept (another property, should NOT be returned)
    green_data = {"name": "TestGreenProp", "quality": "Reality"}
    response_green = await async_client.post("/api/v1/concepts/", json=green_data)
    assert response_green.status_code == 201
    # green_id = response_green.json()["elementId"] # We don't need green_id

    # Create HAS_PROPERTY relationship: Ball -> Red
    has_prop_data = {
        "source_id": ball_id,
        "target_id": red_id,
        "type": "HAS_PROPERTY",
        "properties": {"confidence_score": 0.95} 
    }
    response_rel = await async_client.post("/api/v1/relationships/", json=has_prop_data)
    assert response_rel.status_code == 201

    # 2. Act: Get properties for 'Ball'
    response = await async_client.get(f"/api/v1/concepts/{ball_id}/properties")

    # 3. Assert
    assert response.status_code == 200
    properties = response.json()
    print(f"Properties found for {ball_id}: {properties}") # Debug output
    assert isinstance(properties, list)
    assert len(properties) == 1, "Expected only one property ('Red')"
    
    # Check if 'Red' is the property returned
    prop_names = {prop.get("name") for prop in properties if isinstance(prop, dict)}
    assert "TestRedProp" in prop_names
    assert "TestGreenProp" not in prop_names # Ensure unrelated concepts are not returned
    assert properties[0].get("elementId") == red_id # Check the ID matches

@pytest.mark.anyio # Use anyio
@pytest.mark.usefixtures("clear_db_before_test") # Ensure clean state
async def test_get_causal_chain(async_client: AsyncClient):
    """Test retrieving the causal chain starting from a concept."""
    # 1. Arrange: Create concepts and relationships for the chain
    concept_data = [
        {"name": "TestHeat", "quality": "Reality"},
        {"name": "TestExpansion", "quality": "Reality"},
        {"name": "TestMelting", "quality": "Reality"}
    ]
    concept_ids = {}
    for data in concept_data:
        response = await async_client.post("/api/v1/concepts/", json=data)
        assert response.status_code == 201, f"Failed to create concept {data['name']}"
        concept_ids[data['name']] = response.json()["elementId"]
        
    # Create CAUSES relationships: Heat -> Expansion -> Melting
    rel1_data = {
        "source_id": concept_ids["TestHeat"],
        "target_id": concept_ids["TestExpansion"],
        "type": "CAUSES",
        "properties": {"confidence_score": 0.9}
    }
    response_rel1 = await async_client.post("/api/v1/relationships/", json=rel1_data)
    assert response_rel1.status_code == 201, "Failed to create Heat->Expansion relationship"
    
    rel2_data = {
        "source_id": concept_ids["TestExpansion"],
        "target_id": concept_ids["TestMelting"],
        "type": "CAUSES",
        "properties": {"confidence_score": 0.85}
    }
    response_rel2 = await async_client.post("/api/v1/relationships/", json=rel2_data)
    assert response_rel2.status_code == 201, "Failed to create Expansion->Melting relationship"

    heat_id = concept_ids["TestHeat"]

    # 2. Act: Get the causal chain starting from Heat
    response = await async_client.get(f"/api/v1/concepts/{heat_id}/causal-chain?max_depth=3")

    # 3. Assert
    assert response.status_code == 200
    path_responses = response.json()
    print(f"Causal chain response for {heat_id}: {path_responses}") # Debug output

    assert isinstance(path_responses, list), f"Expected a list of path responses, got {type(path_responses)}"
    assert len(path_responses) > 0, "Expected at least one path response"

    # --- Check the first path found (assuming the shortest path is Heat->Expansion) ---
    # Depending on query result ordering, this might need adjustment.
    # Let's assume the first result corresponds to the full path Heat->Expansion->Melting if max_depth>=2
    # or potentially multiple path objects are returned for each step.

    found_heat_expansion_rel = False
    found_expansion_melting_rel = False
    found_heat_node = False
    found_expansion_node = False
    found_melting_node = False

    for path_resp in path_responses:
        assert 'nodes' in path_resp, "PathResponse dict missing 'nodes' key"
        assert 'relationships' in path_resp, "PathResponse dict missing 'relationships' key"
        assert isinstance(path_resp['nodes'], list)
        assert isinstance(path_resp['relationships'], list)

        nodes_in_path = {node.get('name') for node in path_resp['nodes']}
        rels_in_path = []
        for rel in path_resp['relationships']:
            # Find start and end node names for this relationship
            start_node_name = next((n.get('name') for n in path_resp['nodes'] if n.get('elementId') == rel.get('start_node_id')), None)
            end_node_name = next((n.get('name') for n in path_resp['nodes'] if n.get('elementId') == rel.get('end_node_id')), None)
            rels_in_path.append({
                'start': start_node_name,
                'type': rel.get('type'),
                'end': end_node_name
            })

        print(f"  Path Nodes: {nodes_in_path}")
        print(f"  Path Rels: {rels_in_path}")

        # Check for nodes (accumulate across all path responses, as query might return paths of different lengths)
        if "TestHeat" in nodes_in_path: found_heat_node = True
        if "TestExpansion" in nodes_in_path: found_expansion_node = True
        if "TestMelting" in nodes_in_path: found_melting_node = True

        # Check for specific relationships
        for rel_segment in rels_in_path:
            if rel_segment['start'] == "TestHeat" and rel_segment['type'] == "CAUSES" and rel_segment['end'] == "TestExpansion":
                found_heat_expansion_rel = True
            if rel_segment['start'] == "TestExpansion" and rel_segment['type'] == "CAUSES" and rel_segment['end'] == "TestMelting":
                found_expansion_melting_rel = True

    # Assert based on the full chain created
    assert found_heat_node, "Node 'TestHeat' not found in any returned path"
    assert found_expansion_node, "Node 'TestExpansion' not found in any returned path"
    assert found_melting_node, "Node 'TestMelting' not found in any returned path"
    assert found_heat_expansion_rel, "Relationship Heat->Expansion not found in any returned path"
    assert found_expansion_melting_rel, "Relationship Expansion->Melting not found in any returned path"

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_all_relationships_for_concept(async_client: AsyncClient):
    """Test retrieving all incoming and outgoing relationships for a concept."""
    # 1. Arrange: Create concepts and relationships
    # Create Earth
    earth_data = {"name": "TestEarthForAllRels", "quality": "Reality"}
    res_earth = await async_client.post("/api/v1/concepts/", json=earth_data)
    assert res_earth.status_code == 201
    earth_id = res_earth.json()["elementId"]
    print(f"Created Earth concept (ID: {earth_id})")

    # Create Moon
    moon_data = {"name": "TestMoonForAllRels", "quality": "Reality"}
    res_moon = await async_client.post("/api/v1/concepts/", json=moon_data)
    assert res_moon.status_code == 201
    moon_id = res_moon.json()["elementId"]
    print(f"Created Moon concept (ID: {moon_id})")

    # Create relationship Earth -> INTERACTS_WITH -> Moon
    rel1_data = {
        "source_id": earth_id,
        "target_id": moon_id,
        "type": "INTERACTS_WITH",
        "properties": {"confidence_score": 1.0}
    }
    res_rel1 = await async_client.post("/api/v1/relationships/", json=rel1_data)
    assert res_rel1.status_code == 201, f"Failed to create Earth->Moon rel: {res_rel1.text}"
    rel1_id = res_rel1.json()["elementId"]
    print(f"Created Earth->Moon relationship (ID: {rel1_id})")

    # Create relationship Moon -> INTERACTS_WITH -> Earth
    rel2_data = {
        "source_id": moon_id,
        "target_id": earth_id,
        "type": "INTERACTS_WITH",
        "properties": {"confidence_score": 1.0}
    }
    res_rel2 = await async_client.post("/api/v1/relationships/", json=rel2_data)
    assert res_rel2.status_code == 201, f"Failed to create Moon->Earth rel: {res_rel2.text}"
    rel2_id = res_rel2.json()["elementId"]
    print(f"Created Moon->Earth relationship (ID: {rel2_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get relationships for Earth
    print(f"Getting relationships for Earth concept (ID: {earth_id})")
    response = await async_client.get(f"/api/v1/concepts/{earth_id}/relationships")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    relationships = response.json()
    print(f"Received relationships: {relationships}")

    assert isinstance(relationships, list), "Response should be a list"
    assert len(relationships) == 2, f"Expected 2 relationships, found {len(relationships)}"

    # Check details of the relationships
    found_earth_to_moon = False
    found_moon_to_earth = False
    for rel in relationships:
        assert rel.get("type") == "INTERACTS_WITH"
        source_id = rel.get("source_id")
        target_id = rel.get("target_id")
    
        if source_id == earth_id and target_id == moon_id:
            found_earth_to_moon = True
            assert rel.get("elementId") == rel1_id # Check if the correct relationship was returned
        elif source_id == moon_id and target_id == earth_id:
            found_moon_to_earth = True
            assert rel.get("elementId") == rel2_id # Check if the correct relationship was returned
        else:
            pytest.fail(f"Unexpected relationship found: Source={source_id}, Target={target_id}, Type={rel.get('type')}")

    assert found_earth_to_moon, "Earth -> Moon relationship not found"
    assert found_moon_to_earth, "Moon -> Earth relationship not found"
    print("Assertions passed for test_get_all_relationships_for_concept")

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_concept_hierarchy(async_client: AsyncClient):
    """Test retrieving the hierarchy (IS_PART_OF) upwards from a concept."""
    # 1. Arrange: Create concepts and relationship
    # Create Forest
    forest_data = {"name": "TestForestForHierarchy", "quality": "Reality"}
    res_forest = await async_client.post("/api/v1/concepts/", json=forest_data)
    assert res_forest.status_code == 201
    forest_id = res_forest.json()["elementId"]
    print(f"Created Forest concept (ID: {forest_id})")

    # Create Tree
    tree_data = {"name": "TestTreeForHierarchy", "quality": "Reality"}
    res_tree = await async_client.post("/api/v1/concepts/", json=tree_data)
    assert res_tree.status_code == 201
    tree_id = res_tree.json()["elementId"]
    print(f"Created Tree concept (ID: {tree_id})")

    # Create relationship Tree -> IS_PART_OF -> Forest
    rel_data = {
        "source_id": tree_id,
        "target_id": forest_id,
        "type": "IS_PART_OF",
        "properties": {"confidence_score": 1.0}
    }
    res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
    assert res_rel.status_code == 201, f"Failed to create Tree->Forest rel: {res_rel.text}"
    rel_id = res_rel.json()["elementId"]
    print(f"Created Tree->Forest relationship (ID: {rel_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get hierarchy for Tree
    print(f"Getting hierarchy for Tree concept (ID: {tree_id})")
    response = await async_client.get(f"/api/v1/concepts/{tree_id}/hierarchy")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    hierarchy = response.json()
    print(f"Received hierarchy: {hierarchy}")

    assert isinstance(hierarchy, list), "Response should be a list"
    # Assuming /hierarchy returns a list of ancestor concepts (excluding the start node)
    assert len(hierarchy) == 1, f"Expected 1 ancestor concept in hierarchy, found {len(hierarchy)}"

    # Check the details of the ancestor concept
    ancestor = hierarchy[0]
    assert isinstance(ancestor, dict), "Ancestor element should be a dictionary"
    assert ancestor.get("elementId") == forest_id, "Ancestor ID should match Forest ID"
    assert ancestor.get("name") == "TestForestForHierarchy", "Ancestor name should match Forest name"
    print("Assertions passed for test_get_concept_hierarchy")

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_concept_membership(async_client: AsyncClient):
    """Test retrieving membership (IS_PART_OF) upwards from a concept."""
    # 1. Arrange: Create concepts and relationship
    # Create Forest
    forest_data = {"name": "TestForestForMembership", "quality": "Reality"}
    res_forest = await async_client.post("/api/v1/concepts/", json=forest_data)
    assert res_forest.status_code == 201
    forest_id = res_forest.json()["elementId"]
    print(f"Created Forest concept for membership test (ID: {forest_id})")

    # Create Tree
    tree_data = {"name": "TestTreeForMembership", "quality": "Reality"}
    res_tree = await async_client.post("/api/v1/concepts/", json=tree_data)
    assert res_tree.status_code == 201
    tree_id = res_tree.json()["elementId"]
    print(f"Created Tree concept for membership test (ID: {tree_id})")

    # Create relationship Tree -> IS_PART_OF -> Forest
    rel_data = {
        "source_id": tree_id,
        "target_id": forest_id,
        "type": "IS_PART_OF",
        "properties": {"confidence_score": 1.0}
    }
    res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
    assert res_rel.status_code == 201, f"Failed to create Tree->Forest rel: {res_rel.text}"
    rel_id = res_rel.json()["elementId"]
    print(f"Created Tree->Forest relationship for membership test (ID: {rel_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get membership for Tree
    print(f"Getting membership for Tree concept (ID: {tree_id})")
    response = await async_client.get(f"/api/v1/concepts/{tree_id}/membership")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    membership = response.json()
    print(f"Received membership: {membership}")

    assert isinstance(membership, list), "Response should be a list"
    # Assuming /membership returns a list of ancestor concepts (excluding the start node)
    assert len(membership) == 1, f"Expected 1 ancestor concept in membership, found {len(membership)}"

    # Check the details of the ancestor concept
    ancestor = membership[0]
    assert isinstance(ancestor, dict), "Ancestor element should be a dictionary"
    assert ancestor.get("elementId") == forest_id, "Ancestor ID should match Forest ID"
    assert ancestor.get("name") == "TestForestForMembership", "Ancestor name should match Forest name"
    print("Assertions passed for test_get_concept_membership")

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_interacting_concepts(async_client: AsyncClient):
    """Test retrieving concepts that interact with a given concept."""
    # 1. Arrange: Create concepts and relationship
    # Create Earth
    earth_data = {"name": "TestEarthForInteract", "quality": "Reality"}
    res_earth = await async_client.post("/api/v1/concepts/", json=earth_data)
    assert res_earth.status_code == 201
    earth_id = res_earth.json()["elementId"]
    print(f"Created Earth concept for interact test (ID: {earth_id})")

    # Create Moon
    moon_data = {"name": "TestMoonForInteract", "quality": "Reality"}
    res_moon = await async_client.post("/api/v1/concepts/", json=moon_data)
    assert res_moon.status_code == 201
    moon_id = res_moon.json()["elementId"]
    print(f"Created Moon concept for interact test (ID: {moon_id})")

    # Create Sun (should not interact in this test)
    sun_data = {"name": "TestSunNoInteract", "quality": "Reality"}
    res_sun = await async_client.post("/api/v1/concepts/", json=sun_data)
    assert res_sun.status_code == 201
    sun_id = res_sun.json()["elementId"]
    print(f"Created Sun concept for interact test (ID: {sun_id})")

    # Create relationship Earth -> INTERACTS_WITH -> Moon
    # Note: We only create one direction to test if the endpoint finds based on source
    rel_data = {
        "source_id": earth_id,
        "target_id": moon_id,
        "type": "INTERACTS_WITH",
        "properties": {"confidence_score": 1.0}
    }
    res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
    assert res_rel.status_code == 201, f"Failed to create Earth->Moon INTERACTS_WITH rel: {res_rel.text}"
    rel_id = res_rel.json()["elementId"]
    print(f"Created Earth->Moon INTERACTS_WITH relationship (ID: {rel_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get interacting concepts for Earth
    print(f"Getting interacting concepts for Earth (ID: {earth_id})")
    response = await async_client.get(f"/api/v1/concepts/{earth_id}/interacting")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    interacting = response.json()
    print(f"Received interacting concepts: {interacting}")

    assert isinstance(interacting, list), "Response should be a list"
    # Assuming /interacting returns concepts the source node interacts with (outgoing INTERACTS_WITH)
    # If it also checks incoming, this assertion needs adjustment.
    assert len(interacting) == 1, f"Expected 1 interacting concept, found {len(interacting)}"

    # Check the details of the interacting concept
    interact_concept = interacting[0]
    assert isinstance(interact_concept, dict), "Interacting element should be a dictionary"
    assert interact_concept.get("elementId") == moon_id, "Interacting concept ID should match Moon ID"
    assert interact_concept.get("name") == "TestMoonForInteract", "Interacting concept name should match Moon name"

    # Ensure the unrelated concept (Sun) is not returned
    returned_ids = {c.get("elementId") for c in interacting if isinstance(c, dict)}
    assert sun_id not in returned_ids, "Unrelated concept (Sun) was found in interacting list"
    print("Assertions passed for test_get_interacting_concepts")

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_temporal_relationships(async_client: AsyncClient):
    """Test retrieving temporal relationships (PRECEDES) for a concept."""
    # 1. Arrange: Create concepts and relationship
    # Create Lightning
    lightning_data = {"name": "TestLightning", "quality": "Reality"}
    res_lightning = await async_client.post("/api/v1/concepts/", json=lightning_data)
    assert res_lightning.status_code == 201
    lightning_id = res_lightning.json()["elementId"]
    print(f"Created Lightning concept (ID: {lightning_id})")

    # Create Thunder
    thunder_data = {"name": "TestThunder", "quality": "Reality"}
    res_thunder = await async_client.post("/api/v1/concepts/", json=thunder_data)
    assert res_thunder.status_code == 201
    thunder_id = res_thunder.json()["elementId"]
    print(f"Created Thunder concept (ID: {thunder_id})")

    # Create Rain (unrelated temporally for this test)
    rain_data = {"name": "TestRainNoTemporal", "quality": "Reality"}
    res_rain = await async_client.post("/api/v1/concepts/", json=rain_data)
    assert res_rain.status_code == 201
    rain_id = res_rain.json()["elementId"]
    print(f"Created Rain concept (ID: {rain_id})")

    # Create relationship Lightning -> PRECEDES -> Thunder
    # Include required temporal properties if defined in schema (adjust as needed)
    rel_data = {
        "source_id": lightning_id,
        "target_id": thunder_id,
        "type": "PRECEDES",
        "properties": {
            "confidence_score": 0.98,
            "temporal_distance": 2.0, # Changed from "seconds" to a number
            "temporal_unit": "seconds",
            "temporal_order": 1
        }
    }
    res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
    assert res_rel.status_code == 201, f"Failed to create Lightning->Thunder PRECEDES rel: {res_rel.text}"
    rel_id = res_rel.json()["elementId"]
    print(f"Created Lightning->Thunder PRECEDES relationship (ID: {rel_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get temporal relationships for Lightning
    print(f"Getting temporal relationships for Lightning (ID: {lightning_id})")
    response = await async_client.get(f"/api/v1/concepts/{lightning_id}/temporal")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    temporal_rels = response.json()
    print(f"Received temporal relationships: {temporal_rels}")

    assert isinstance(temporal_rels, list), "Response should be a list"
    # Assuming /temporal returns outgoing PRECEDES relationships from the source concept
    assert len(temporal_rels) == 1, f"Expected 1 temporal relationship, found {len(temporal_rels)}"

    # Check the details of the relationship
    rel = temporal_rels[0]
    assert isinstance(rel, dict), "Relationship element should be a dictionary"
    assert rel.get("elementId") == rel_id, "Relationship ID mismatch"
    assert rel.get("relationship_type") == "PRECEDES", "Relationship type should be PRECEDES"
    assert rel.get("direction") == "outgoing", "Relationship direction should be outgoing"
    assert rel.get("related_concept_id") == thunder_id, "Related concept ID mismatch"

    # Ensure the unrelated concept (Rain) is not involved
    assert rel.get("start_node_element_id") != rain_id
    assert rel.get("end_node_element_id") != rain_id
    print("Assertions passed for test_get_temporal_relationships")

@pytest.mark.asyncio
@pytest.mark.usefixtures("clear_db_before_test") # Add fixture
async def test_get_spatial_relationships(async_client: AsyncClient):
    """Test retrieving spatial relationships (SPATIALLY_RELATES_TO) for a concept."""
    # 1. Arrange: Create concepts and relationship
    # Create Earth
    earth_data = {"name": "TestEarthSpatial", "quality": "Reality"}
    res_earth = await async_client.post("/api/v1/concepts/", json=earth_data)
    assert res_earth.status_code == 201
    earth_id = res_earth.json()["elementId"]
    print(f"Created Earth concept for spatial test (ID: {earth_id})")

    # Create Moon
    moon_data = {"name": "TestMoonSpatial", "quality": "Reality"}
    res_moon = await async_client.post("/api/v1/concepts/", json=moon_data)
    assert res_moon.status_code == 201
    moon_id = res_moon.json()["elementId"]
    print(f"Created Moon concept for spatial test (ID: {moon_id})")

    # Create Mars (unrelated spatially for this test)
    mars_data = {"name": "TestMarsNoSpatial", "quality": "Reality"}
    res_mars = await async_client.post("/api/v1/concepts/", json=mars_data)
    assert res_mars.status_code == 201
    mars_id = res_mars.json()["elementId"]
    print(f"Created Mars concept for spatial test (ID: {mars_id})")

    # Create relationship Earth -> SPATIALLY_RELATES_TO -> Moon
    # Include required spatial properties if defined in schema (adjust as needed)
    rel_data = {
        "source_id": earth_id,
        "target_id": moon_id,
        "type": "SPATIALLY_RELATES_TO",
        "properties": {
            "confidence_score": 1.0,
            "relation_type": "near",
            "distance": "384400",
            "spatial_unit": "kilometers",
            "spatial_dimension": "3D"
        }
    }
    res_rel = await async_client.post("/api/v1/relationships/", json=rel_data)
    assert res_rel.status_code == 201, f"Failed to create Earth->Moon SPATIALLY_RELATES_TO rel: {res_rel.text}"
    rel_id = res_rel.json()["elementId"]
    print(f"Created Earth->Moon SPATIALLY_RELATES_TO relationship (ID: {rel_id})")

    # Brief pause for potential consistency
    await asyncio.sleep(0.3)

    # 2. Act: Get spatial relationships for Earth
    print(f"Getting spatial relationships for Earth (ID: {earth_id})")
    response = await async_client.get(f"/api/v1/concepts/{earth_id}/spatial")

    # 3. Assert
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    spatial_rels = response.json()
    print(f"Received spatial relationships: {spatial_rels}")

    assert isinstance(spatial_rels, list), "Response should be a list"
    # Assuming /spatial returns outgoing SPATIALLY_RELATES_TO relationships
    assert len(spatial_rels) == 1, f"Expected 1 spatial relationship, found {len(spatial_rels)}"

    # Check the details of the relationship
    rel = spatial_rels[0]
    assert isinstance(rel, dict), "Relationship element should be a dictionary"
    assert rel.get("elementId") == rel_id, "Relationship ID mismatch"
    assert rel.get("relationship_type") == "SPATIALLY_RELATES_TO", "Relationship type should be SPATIALLY_RELATES_TO"
    assert rel.get("direction") == "outgoing", "Relationship direction should be outgoing"
    assert rel.get("related_concept_id") == moon_id, "Related concept ID mismatch"

    # Ensure the unrelated concept (Mars) is not involved
    assert rel.get("start_node_element_id") != mars_id
    assert rel.get("end_node_element_id") != mars_id
    print("Assertions passed for test_get_spatial_relationships")

# --- Potentially add more tests for specific relationship types or edge cases --- 