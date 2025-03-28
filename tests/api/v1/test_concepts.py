from fastapi.testclient import TestClient
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from typing import List, Dict, Any
import collections # For comparing lists regardless of order

# Import your FastAPI application instance
from src.main import app

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
async def test_get_concepts_by_confidence_high_threshold(load_sample_data, async_client: AsyncClient):
    """Test retrieving concepts with a high confidence threshold using GET /."""
    # Use root path with query parameter
    response = await async_client.get("/api/v1/concepts", params={"confidence_threshold": 0.9, "limit": 10})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Assuming sample data has concepts with high confidence
    for concept in data:
        assert concept.get("confidence", 0) >= 0.9
    # ... other specific assertions ...

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
@pytest.mark.anyio
async def test_get_concepts_by_category_relation(load_sample_data, async_client: AsyncClient): # Fixture name stays the same
    """Test retrieving concepts classified under the 'Relation' category."""
    response = await async_client.get("/api/v1/concepts", params={"category_name": "Relation"})
    assert response.status_code == status.HTTP_200_OK
    concepts = response.json()

    # --- Assertions based on sample data for 'Relation' category ---
    assert isinstance(concepts, list), "Response should be a list of concepts"
    assert len(concepts) > 0, f"Expected concepts for category 'Relation', but got none."

    # Check presence of concepts expected to be under Relation (via Causality or Community)
    expected_concept_names = {"Heat", "Expansion", "Earth", "Moon", "Lightning", "Thunder"}
    returned_concept_names = {c['name'] for c in concepts if 'name' in c}

    assert expected_concept_names.issubset(returned_concept_names), \
        f"Missing expected concepts for category 'Relation': {expected_concept_names - returned_concept_names}"

    # Check absence of concepts NOT under Relation
    unexpected_concept_names = {"Ball", "Red", "Forest", "Tree", "Atom", "Shadow", "Vacuum"}
    assert not any(name in returned_concept_names for name in unexpected_concept_names), \
        f"Found unexpected concepts for category 'Relation': {[n for n in unexpected_concept_names if n in returned_concept_names]}"

    # Verify structure of returned concepts (optional but good)
    for concept in concepts:
        assert "id" in concept
        assert "name" in concept
        # Add other checks as needed based on the API response model for this endpoint

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
KNOWN_IDS = {
     "Ball": "ball_id_placeholder", # Replace with actual ID
     "Red": "red_id_placeholder",
     "Heat": "heat_id_placeholder",
     "Expansion": "expansion_id_placeholder",
     "Earth": "earth_id_placeholder",
     "Moon": "moon_id_placeholder",
     "Lightning": "lightning_id_placeholder",
     "Thunder": "thunder_id_placeholder",
     "Forest": "forest_id_placeholder",
     "Tree": "tree_id_placeholder",
}
# Function to get ID, replace with actual call if helper is implemented
def get_id(name: str) -> str:
    id_val = KNOWN_IDS.get(name)
    if not id_val or "placeholder" in id_val:
         pytest.skip(f"Skipping test, actual ID for '{name}' not configured in KNOWN_IDS")
    return id_val

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "category_name, expected_present, expected_absent",
    [
        ("Quantity", EXPECTED_CONCEPTS_BY_CATEGORY["Quantity"], UNEXPECTED_CONCEPTS_BY_CATEGORY["Quantity"]),
        ("Relation", EXPECTED_CONCEPTS_BY_CATEGORY["Relation"], UNEXPECTED_CONCEPTS_BY_CATEGORY["Relation"]),
    ]
)
async def test_get_concepts_by_category_relation(
    async_client: AsyncClient, category_name: str, expected_present: List[str], expected_absent: List[str]
):
    # ... (Keep the implementation from the previous step using collections.Counter) ...
    """
    Tests retrieving concepts classified under Quantity or Relation categories
    using the INSTANCE_OF relationship to their Subcategories.
    """
    print(f"\nTesting category (via INSTANCE_OF): {category_name}")
    response = await async_client.get(f"/api/v1/concepts?category_name={category_name}&limit=200")

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"

    try:
        concepts = response.json()
        if not isinstance(concepts, list):
             pytest.fail(f"Expected response to be a list, but got {type(concepts)}. Response: {response.text}")

        concept_names = sorted([c['name'] for c in concepts if isinstance(c, dict) and 'name' in c])
        print(f"Found concepts for {category_name}: {concept_names}")

    except Exception as e:
        pytest.fail(f"Failed to parse JSON response or extract concept names. Error: {e}. Response: {response.text}")

    sorted_expected_present = sorted(expected_present)
    assert collections.Counter(concept_names) == collections.Counter(sorted_expected_present), \
        f"Mismatch for category '{category_name}'. Expected: {sorted_expected_present}. Found: {concept_names}"

    found_unexpected = [name for name in expected_absent if name in concept_names]
    assert not found_unexpected, f"Found unexpected concepts for category '{category_name}': {found_unexpected}. Found: {concept_names}"

@pytest.mark.asyncio
async def test_get_concepts_root(async_client: AsyncClient):
    # ... (Keep implementation) ...
    """ Tests retrieving concepts from the root endpoint without filters. """
    print("\nTesting GET /api/v1/concepts (root)")
    response = await async_client.get("/api/v1/concepts?limit=10")
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    print(f"Found {len(concepts)} root concepts (limit 10). Sample: {[c.get('name') for c in concepts[:3]]}")

@pytest.mark.asyncio
async def test_get_concepts_nonexistent_category(async_client: AsyncClient):
    # ... (Keep implementation) ...
    """ Tests filtering by a category name that doesn't exist. """
    print("\nTesting GET /api/v1/concepts?category_name=DoesNotExist")
    response = await async_client.get("/api/v1/concepts?category_name=DoesNotExist")
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    assert len(concepts) == 0
    print("Successfully received empty list for non-existent category.")

# --- NEW Tests for GET /concepts filters ---

@pytest.mark.asyncio
async def test_get_concepts_by_subcategory(async_client: AsyncClient):
    """ Tests filtering concepts by subcategory name. """
    subcategory_name = "Causality" # Example from sample data
    expected_concepts = ["Heat", "Expansion", "Lightning", "Thunder"] # Based on sample data
    print(f"\nTesting GET /api/v1/concepts?subcategory_name={subcategory_name}")
    response = await async_client.get(f"/api/v1/concepts?subcategory_name={subcategory_name}&limit=50")

    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    concept_names = sorted([c['name'] for c in concepts])
    assert collections.Counter(concept_names) == collections.Counter(sorted(expected_concepts)), \
        f"Mismatch for subcategory '{subcategory_name}'. Expected: {sorted(expected_concepts)}. Found: {concept_names}"

@pytest.mark.asyncio
async def test_get_concepts_by_confidence(async_client: AsyncClient):
    """ Tests filtering concepts by minimum confidence score. """
    threshold = 0.99 # Concepts like Atom (0.98), Shadow (0.95), Vacuum (0.97) should be excluded
    expected_present = ["Ball", "Red", "Heat", "Expansion", "Earth", "Moon", "Forest", "Tree", "Lightning", "Thunder", "Absence", "Horizon", "Unicorn", "Gravity"] # Concepts with 1.0
    print(f"\nTesting GET /api/v1/concepts?confidence_threshold={threshold}")
    response = await async_client.get(f"/api/v1/concepts?confidence_threshold={threshold}&limit=100")

    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    concept_names = sorted([c['name'] for c in concepts])
    assert collections.Counter(concept_names) == collections.Counter(sorted(expected_present)), \
         f"Mismatch for confidence >= {threshold}. Expected: {sorted(expected_present)}. Found: {concept_names}"
    # Optionally check absence
    assert "Atom" not in concept_names
    assert "Shadow" not in concept_names
    assert "Vacuum" not in concept_names

@pytest.mark.asyncio
async def test_get_concepts_pagination(async_client: AsyncClient):
    """ Tests limit and skip parameters. """
    print(f"\nTesting GET /api/v1/concepts pagination")
    # Get first 2 concepts
    response1 = await async_client.get(f"/api/v1/concepts?limit=2&skip=0&sort_by=name") # Assuming sorting for predictability
    assert response1.status_code == 200
    concepts1 = response1.json()
    assert isinstance(concepts1, list)
    assert len(concepts1) == 2
    names1 = [c['name'] for c in concepts1]

    # Get next 2 concepts
    response2 = await async_client.get(f"/api/v1/concepts?limit=2&skip=2&sort_by=name")
    assert response2.status_code == 200
    concepts2 = response2.json()
    assert isinstance(concepts2, list)
    assert len(concepts2) == 2
    names2 = [c['name'] for c in concepts2]

    # Ensure the pages are different and don't overlap (assuming sorting)
    assert names1 != names2
    assert names1[0] != names2[0] # Basic check
    print(f"Page 1: {names1}, Page 2: {names2}")
    # NOTE: Requires adding a sort_by parameter to the API endpoint for deterministic pagination testing

# --- NEW Tests for Relationship Endpoints ---

@pytest.mark.asyncio
async def test_get_concept_properties(async_client: AsyncClient):
    """ Tests GET /{concept_id}/properties """
    ball_id = get_id("Ball")
    print(f"\nTesting GET /api/v1/concepts/{ball_id}/properties")
    response = await async_client.get(f"/api/v1/concepts/{ball_id}/properties")
    assert response.status_code == 200
    properties = response.json()
    assert isinstance(properties, list)
    prop_names = {p['name'] for p in properties}
    assert "Red" in prop_names # Ball HAS_PROPERTY Red
    # Add checks for absence if needed

@pytest.mark.asyncio
async def test_get_causal_chain(async_client: AsyncClient):
    """ Tests GET /{concept_id}/causal-chain """
    heat_id = get_id("Heat")
    print(f"\nTesting GET /api/v1/concepts/{heat_id}/causal-chain")
    response = await async_client.get(f"/api/v1/concepts/{heat_id}/causal-chain?max_depth=1")
    assert response.status_code == 200
    paths = response.json()
    assert isinstance(paths, list)
    assert len(paths) > 0 # Expecting at least one path
    # Check if a path contains Heat -> Expansion
    found_path = False
    for path in paths:
        nodes = path.get('nodes', [])
        if len(nodes) == 2 and nodes[0].get('name') == 'Heat' and nodes[1].get('name') == 'Expansion':
             found_path = True
             break
    assert found_path, f"Expected path Heat->Expansion not found in {paths}"

@pytest.mark.asyncio
async def test_get_all_relationships_for_concept(async_client: AsyncClient):
    """ Tests GET /{concept_id}/relationships """
    earth_id = get_id("Earth")
    print(f"\nTesting GET /api/v1/concepts/{earth_id}/relationships")
    response = await async_client.get(f"/api/v1/concepts/{earth_id}/relationships?limit=10")
    assert response.status_code == 200
    relationships = response.json()
    assert isinstance(relationships, list)
    assert len(relationships) > 0
    # Check for specific relationships, e.g., Earth INSTANCE_OF Community, Earth INTERACTS_WITH Moon
    rel_types_and_targets = {(r.get('relationship_type'), r.get('end_node_name')) for r in relationships}
    assert ('INSTANCE_OF', 'Community') in rel_types_and_targets
    assert ('INTERACTS_WITH', 'Moon') in rel_types_and_targets
    assert ('SPATIALLY_RELATES_TO', 'Moon') in rel_types_and_targets

@pytest.mark.asyncio
async def test_get_concept_hierarchy(async_client: AsyncClient):
    """ Tests GET /{concept_id}/hierarchy """
    forest_id = get_id("Forest")
    print(f"\nTesting GET /api/v1/concepts/{forest_id}/hierarchy")
    response = await async_client.get(f"/api/v1/concepts/{forest_id}/hierarchy?max_depth=1")
    assert response.status_code == 200
    paths = response.json()
    assert isinstance(paths, list)
    # Check for Forest -> CONTAINS -> Tree path
    found_path = False
    for path in paths:
        nodes = path.get('nodes', [])
        relationships = path.get('relationships', [])
        if len(nodes) == 2 and nodes[0].get('name') == 'Forest' and nodes[1].get('name') == 'Tree' \
           and len(relationships) == 1 and relationships[0].get('type') == 'CONTAINS':
             found_path = True
             break
    assert found_path, f"Expected path Forest-CONTAINS->Tree not found in {paths}"

@pytest.mark.asyncio
async def test_get_concept_membership(async_client: AsyncClient):
    """ Tests GET /{concept_id}/membership """
    tree_id = get_id("Tree")
    print(f"\nTesting GET /api/v1/concepts/{tree_id}/membership")
    response = await async_client.get(f"/api/v1/concepts/{tree_id}/membership?max_depth=1")
    assert response.status_code == 200
    paths = response.json()
    assert isinstance(paths, list)
    # Check for Tree -> IS_PART_OF -> Forest path
    found_path = False
    for path in paths:
        nodes = path.get('nodes', [])
        relationships = path.get('relationships', [])
        if len(nodes) == 2 and nodes[0].get('name') == 'Tree' and nodes[1].get('name') == 'Forest' \
           and len(relationships) == 1 and relationships[0].get('type') == 'IS_PART_OF':
             found_path = True
             break
    assert found_path, f"Expected path Tree-IS_PART_OF->Forest not found in {paths}"


@pytest.mark.asyncio
async def test_get_interacting_concepts(async_client: AsyncClient):
    """ Tests GET /{concept_id}/interacting """
    moon_id = get_id("Moon")
    print(f"\nTesting GET /api/v1/concepts/{moon_id}/interacting")
    response = await async_client.get(f"/api/v1/concepts/{moon_id}/interacting")
    assert response.status_code == 200
    interacting = response.json()
    assert isinstance(interacting, list)
    names = {c['name'] for c in interacting}
    assert 'Earth' in names # Moon INTERACTS_WITH Earth

@pytest.mark.asyncio
async def test_get_temporal_relationships(async_client: AsyncClient):
    """ Tests GET /{concept_id}/temporal """
    lightning_id = get_id("Lightning")
    print(f"\nTesting GET /api/v1/concepts/{lightning_id}/temporal")
    response = await async_client.get(f"/api/v1/concepts/{lightning_id}/temporal")
    assert response.status_code == 200
    rels = response.json()
    assert isinstance(rels, list)
    assert len(rels) > 0
    # Check for Lightning PRECEDES Thunder
    found_rel = False
    for rel in rels:
        if rel.get('relationship_type') == 'PRECEDES' and rel.get('end_node_name') == 'Thunder':
            found_rel = True
            break
    assert found_rel, f"Expected Lightning PRECEDES Thunder not found in {rels}"

@pytest.mark.asyncio
async def test_get_spatial_relationships(async_client: AsyncClient):
    """ Tests GET /{concept_id}/spatial """
    moon_id = get_id("Moon")
    print(f"\nTesting GET /api/v1/concepts/{moon_id}/spatial")
    response = await async_client.get(f"/api/v1/concepts/{moon_id}/spatial")
    assert response.status_code == 200
    rels = response.json()
    assert isinstance(rels, list)
    assert len(rels) > 0
    # Check for Moon SPATIALLY_RELATES_TO Earth
    found_rel = False
    for rel in rels:
        if rel.get('relationship_type') == 'SPATIALLY_RELATES_TO' and rel.get('end_node_name') == 'Earth':
            found_rel = True
            # Optionally check properties like rel['properties']['relation_type'] == 'orbits'
            assert rel.get('properties', {}).get('relation_type') == 'orbits'
            break
    assert found_rel, f"Expected Moon SPATIALLY_RELATES_TO Earth not found in {rels}" 