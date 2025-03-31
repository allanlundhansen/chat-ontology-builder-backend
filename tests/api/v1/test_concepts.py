from fastapi.testclient import TestClient
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status
from typing import List, Dict, Any
import collections # For comparing lists regardless of order

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
# KNOWN_IDS = { ... }
# def get_id(name: str) -> str: ...

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

@pytest.mark.asyncio
async def test_get_concepts_by_subcategory(async_client: AsyncClient):
    """Test filtering concepts by subcategory (e.g., Causality)."""
    # Assumes sample data links concepts like Heat/Expansion to Causality
    response = await async_client.get("/api/v1/concepts?subcategory_name=Causality&limit=50")
    assert response.status_code == 200
    concepts = response.json()
    assert isinstance(concepts, list)
    concept_names = {c['name'] for c in concepts}
    assert "Heat" in concept_names
    assert "Expansion" in concept_names

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
async def test_get_all_relationships_for_concept(async_client: AsyncClient):
    """Test retrieving all incoming and outgoing relationships for a concept."""
    # Assumes 'Earth' interacts with 'Moon' (both directions)
    earth_id = get_id("Earth") # Relies on placeholder or helper

    # TODO: Create test data (Earth, Moon) and relationships (INTERACTS_WITH both ways)
    pytest.skip("Skipping test, actual ID for 'Earth' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{earth_id}/relationships")

    assert response.status_code == 200
    relationships = response.json()
    assert isinstance(relationships, list)
    assert len(relationships) >= 2 # Expecting Earth->Moon and Moon->Earth
    # Add more specific assertions about the relationship types, sources, targets

@pytest.mark.asyncio
async def test_get_concept_hierarchy(async_client: AsyncClient):
    """Test retrieving the hierarchy (CONTAINS) upwards from a concept."""
    # Assumes 'Tree' is part of 'Forest'
    tree_id = get_id("Tree") # Relies on placeholder or helper

    # TODO: Create test data (Tree, Forest) and CONTAINS relationship (Forest->Tree)
    pytest.skip("Skipping test, actual ID for 'Tree' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{tree_id}/hierarchy")

    assert response.status_code == 200
    hierarchy = response.json()
    assert isinstance(hierarchy, list) # Or dict
    # Assert that 'Forest' is part of the hierarchy returned

@pytest.mark.asyncio
async def test_get_concept_membership(async_client: AsyncClient):
    """Test retrieving membership (IS_PART_OF) upwards from a concept."""
    # Assumes 'Tree' IS_PART_OF 'Forest'
    tree_id = get_id("Tree") # Relies on placeholder or helper

    # TODO: Create test data (Tree, Forest) and IS_PART_OF relationship (Tree->Forest)
    pytest.skip("Skipping test, actual ID for 'Tree' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{tree_id}/membership")

    assert response.status_code == 200
    membership = response.json()
    assert isinstance(membership, list) # Or dict
    # Assert that 'Forest' is part of the membership path returned

@pytest.mark.asyncio
async def test_get_interacting_concepts(async_client: AsyncClient):
    """Test retrieving concepts that interact with a given concept."""
    # Assumes 'Earth' INTERACTS_WITH 'Moon'
    earth_id = get_id("Earth") # Relies on placeholder or helper

    # TODO: Create test data (Earth, Moon) and INTERACTS_WITH relationship
    pytest.skip("Skipping test, actual ID for 'Earth' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{earth_id}/interacting")

    assert response.status_code == 200
    interacting = response.json()
    assert isinstance(interacting, list)
    # Assert that 'Moon' is in the list of interacting concepts

@pytest.mark.asyncio
async def test_get_temporal_relationships(async_client: AsyncClient):
    """Test retrieving temporal relationships (PRECEDES) for a concept."""
    # Assumes 'Lightning' PRECEDES 'Thunder'
    lightning_id = get_id("Lightning") # Relies on placeholder or helper

    # TODO: Create test data (Lightning, Thunder) and PRECEDES relationship
    pytest.skip("Skipping test, actual ID for 'Lightning' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{lightning_id}/temporal")

    assert response.status_code == 200
    temporal_rels = response.json()
    assert isinstance(temporal_rels, list)
    # Assert that a relationship involving 'Thunder' exists in the list

@pytest.mark.asyncio
async def test_get_spatial_relationships(async_client: AsyncClient):
    """Test retrieving spatial relationships (SPATIALLY_RELATES_TO) for a concept."""
    # Assumes 'Earth' SPATIALLY_RELATES_TO 'Moon'
    earth_id = get_id("Earth") # Relies on placeholder or helper

    # TODO: Create test data (Earth, Moon) and SPATIALLY_RELATES_TO relationship
    pytest.skip("Skipping test, actual ID for 'Earth' and test data creation needed.")

    response = await async_client.get(f"/api/v1/concepts/{earth_id}/spatial")

    assert response.status_code == 200
    spatial_rels = response.json()
    assert isinstance(spatial_rels, list)
    # Assert that a relationship involving 'Moon' exists in the list 