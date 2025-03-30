import pytest
from httpx import AsyncClient
from fastapi import status
from typing import List, Dict, Any
import asyncio # Import asyncio for sleep
import random # Import random for adding randomness

# Define the base endpoint path
RELATIONSHIPS_ENDPOINT = "/api/v1/relationships/"
CONCEPTS_ENDPOINT = "/api/v1/concepts/" # Needed to create nodes

# Helper function to create concepts and relationships for tests
async def create_test_relationship(async_client: AsyncClient, rel_type: str, properties: Dict = None) -> Dict[str, Any]:
    """Creates two concepts and a relationship between them."""
    # Create source concept
    prop_id_str = f"_{properties.get('id')}" if properties and 'id' in properties else ""
    source_concept_name = f"Source_{rel_type}{prop_id_str}_{random.randint(1000, 9999)}" # Add randomness
    source_concept_data = {"name": source_concept_name}
    source_res = await async_client.post(CONCEPTS_ENDPOINT, json=source_concept_data)
    assert source_res.status_code == status.HTTP_201_CREATED, f"Failed to create source concept: {source_res.text}"
    source_id = source_res.json().get("elementId")
    assert source_id

    # Create target concept
    target_concept_name = f"Target_{rel_type}{prop_id_str}_{random.randint(1000, 9999)}" # Add randomness
    target_concept_data = {"name": target_concept_name}
    target_res = await async_client.post(CONCEPTS_ENDPOINT, json=target_concept_data)
    assert target_res.status_code == status.HTTP_201_CREATED, f"Failed to create target concept: {target_res.text}"
    target_id = target_res.json().get("elementId")
    assert target_id

    # Prepare relationship properties
    rel_properties = properties or {"confidence_score": 0.7, "source_information": "default_test_source"}

    # ADDED source_information check/default
    if "source_information" not in rel_properties:
        rel_properties["source_information"] = "default_test_source"

    # Add required properties for specific types if missing
    if rel_type == "SPATIALLY_RELATES_TO":
        if "relation_type" not in rel_properties:
            rel_properties["relation_type"] = "near" # Add default valid relation type
        if "spatial_dimension" not in rel_properties:
             rel_properties["spatial_dimension"] = "3D" # Add default valid spatial dimension
        # Ensure distance and unit are present if expected (based on validator rules)
        if "distance" not in rel_properties:
            rel_properties["distance"] = 1.0 # Add default distance
        if "spatial_unit" not in rel_properties:
            rel_properties["spatial_unit"] = "m" # Add default unit

    # Create relationship using IDs
    rel_data = {
        "type": rel_type,
        "source_id": source_id,
        "target_id": target_id,
        "properties": rel_properties
    }
    rel_res = await async_client.post(RELATIONSHIPS_ENDPOINT, json=rel_data)
    assert rel_res.status_code == status.HTTP_201_CREATED, f"Failed to create relationship '{rel_type}': {rel_res.text}" # Assuming POST relationships returns 201

    created_rel_data = rel_res.json()
    # Store concept names for potential later use if needed, though not returned by endpoint
    created_rel_data['_source_concept_name'] = source_concept_name
    created_rel_data['_target_concept_name'] = target_concept_name
    return created_rel_data


@pytest.mark.anyio
@pytest.mark.usefixtures("manage_db_state")
async def test_list_relationships_success(async_client: AsyncClient):
    """Test retrieving a list of relationships successfully."""
    # Arrange: Ensure at least one relationship exists
    await create_test_relationship(async_client, "TEST_LIST_SUCCESS")

    # Act
    response = await async_client.get(RELATIONSHIPS_ENDPOINT)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert "relationships" in data
    assert "total_count" in data
    assert isinstance(data["relationships"], list)
    assert len(data["relationships"]) >= 1


@pytest.mark.anyio
@pytest.mark.usefixtures("manage_db_state", "clear_db_before_test")
async def test_list_relationships_pagination(async_client: AsyncClient):
    """Test pagination (skip, limit) for listing relationships."""
    # Arrange: Create more relationships than default limit (e.g., 12)
    all_rel_ids = set()
    REL_TYPE = "TEST_PAGINATION" # Define type for reuse
    for i in range(12):
        rel = await create_test_relationship(async_client, REL_TYPE)
        all_rel_ids.add(rel.get("elementId"))
    assert len(all_rel_ids) == 12 # Ensure 12 unique relationships created

    # Act: Get first 5
    max_retries = 3
    retry_delay = 0.3 # seconds

    for attempt in range(max_retries):
        # Add type filter
        response_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"limit": 5, "type": REL_TYPE})
        assert response_limit5.status_code == status.HTTP_200_OK
        data_limit5 = response_limit5.json()
        assert isinstance(data_limit5, dict)
        assert "relationships" in data_limit5
        assert "total_count" in data_limit5
        assert isinstance(data_limit5["relationships"], list)
        if len(data_limit5["relationships"]) == 5:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get 5 relationships after {max_retries} attempts. Got {len(data_limit5['relationships'])}.")

    # Act: Get next 5 (skip 5)
    for attempt in range(max_retries):
        # Add type filter
        response_skip5_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"skip": 5, "limit": 5, "type": REL_TYPE})
        assert response_skip5_limit5.status_code == status.HTTP_200_OK
        data_skip5_limit5 = response_skip5_limit5.json()
        assert isinstance(data_skip5_limit5, dict)
        assert "relationships" in data_skip5_limit5
        assert "total_count" in data_skip5_limit5
        assert isinstance(data_skip5_limit5["relationships"], list)
        if len(data_skip5_limit5["relationships"]) == 5:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get next 5 relationships (skip 5) after {max_retries} attempts. Got {len(data_skip5_limit5['relationships'])}.")

    # Act: Get last 2 (skip 10)
    for attempt in range(max_retries):
        # Add type filter
        response_skip10_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"skip": 10, "limit": 5, "type": REL_TYPE})
        assert response_skip10_limit5.status_code == status.HTTP_200_OK
        data_skip10_limit5 = response_skip10_limit5.json()
        assert isinstance(data_skip10_limit5, dict)
        assert "relationships" in data_skip10_limit5
        assert "total_count" in data_skip10_limit5
        assert isinstance(data_skip10_limit5["relationships"], list)
        # Expecting the remaining 2
        if len(data_skip10_limit5["relationships"]) == 2:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get last 2 relationships (skip 10) after {max_retries} attempts. Got {len(data_skip10_limit5['relationships'])}.")

    # Assert
    assert response_limit5.status_code == status.HTTP_200_OK
    data_limit5 = response_limit5.json()
    assert isinstance(data_limit5, dict)
    assert "relationships" in data_limit5
    assert "total_count" in data_limit5
    assert isinstance(data_limit5["relationships"], list)
    assert len(data_limit5["relationships"]) == 5

    assert response_skip5_limit5.status_code == status.HTTP_200_OK
    data_skip5_limit5 = response_skip5_limit5.json()
    assert isinstance(data_skip5_limit5, dict)
    assert "relationships" in data_skip5_limit5
    assert "total_count" in data_skip5_limit5
    assert isinstance(data_skip5_limit5["relationships"], list)
    assert len(data_skip5_limit5["relationships"]) == 5

    assert response_skip10_limit5.status_code == status.HTTP_200_OK
    data_skip10_limit5 = response_skip10_limit5.json()
    assert isinstance(data_skip10_limit5, dict)
    assert "relationships" in data_skip10_limit5
    assert "total_count" in data_skip10_limit5
    assert isinstance(data_skip10_limit5["relationships"], list)
    assert len(data_skip10_limit5["relationships"]) == 2 # Only 2 remaining

    # Ensure no overlap between pages
    ids_limit5 = {item.get("elementId") for item in data_limit5["relationships"]}
    ids_skip5_limit5 = {item.get("elementId") for item in data_skip5_limit5["relationships"]}
    ids_skip10_limit5 = {item.get("elementId") for item in data_skip10_limit5["relationships"]}

    assert len(ids_limit5.intersection(ids_skip5_limit5)) == 0
    assert len(ids_skip5_limit5.intersection(ids_skip10_limit5)) == 0


@pytest.mark.anyio
@pytest.mark.usefixtures("manage_db_state")
async def test_list_relationships_filter_by_type(async_client: AsyncClient):
    """Test filtering relationships by type."""
    # Arrange: Create relationships of different types
    type_a_rel = await create_test_relationship(async_client, "TYPE_A")
    await create_test_relationship(async_client, "TYPE_B")
    await create_test_relationship(async_client, "TYPE_A", {"id": 2}) # Another TYPE_A

    # Act: Filter by TYPE_A
    max_retries = 3
    retry_delay = 0.3 # seconds
    data = [] # Initialize data

    for attempt in range(max_retries):
        response = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"type": "TYPE_A"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, dict)
        assert "relationships" in data
        assert "total_count" in data
        assert isinstance(data["relationships"], list)
        if len(data["relationships"]) >= 2: # Check if we found at least 2 TYPE_A relationships
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get >= 2 relationships of TYPE_A after {max_retries} attempts. Got {len(data['relationships'])}.")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert "relationships" in data
    assert "total_count" in data
    assert isinstance(data["relationships"], list)
    assert len(data["relationships"]) >= 2 # Should find at least the two we created
    found_correct_type = False
    found_other_type = False
    for item in data["relationships"]:
        assert "type" in item
        if item["type"] == "TYPE_A":
            found_correct_type = True
        else:
            found_other_type = True # Should not happen
        assert "elementId" in item

    assert found_correct_type is True
    assert found_other_type is False # Ensure ONLY TYPE_A was returned


@pytest.mark.anyio
@pytest.mark.usefixtures("clear_db_before_test")
async def test_list_relationships_empty(async_client: AsyncClient):
    """Test listing relationships when none exist or match.
    Relies on the function-scoped manage_db_state fixture to ensure DB is empty.
    """
    # Arrange: DB is cleared by manage_db_state fixture

    # Act: Request relationships
    response = await async_client.get(RELATIONSHIPS_ENDPOINT)

    # Assert: Expect 200 OK and an empty list
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)
    assert "relationships" in data
    assert "total_count" in data
    assert isinstance(data["relationships"], list)
    assert len(data["relationships"]) == 0
    assert isinstance(data["total_count"], int)
    assert data["total_count"] == 0

    # Act: Request relationships with a filter that won't match anything
    response_filtered = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"type": "NON_EXISTENT_TYPE"})

    # Assert: Expect 200 OK and an empty list
    assert response_filtered.status_code == status.HTTP_200_OK
    data_filtered = response_filtered.json()
    assert isinstance(data_filtered, dict)
    assert "relationships" in data_filtered
    assert "total_count" in data_filtered
    assert isinstance(data_filtered["relationships"], list)
    assert len(data_filtered["relationships"]) == 0
    assert data_filtered["total_count"] == 0 # Also check total count


@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data", "clear_db_before_test")
async def test_get_relationship_by_id_success(async_client: AsyncClient):
    """Test retrieving a specific relationship by its element ID successfully."""
    # Arrange: Create source and target concepts
    source_concept_data = {"name": "Test Source Concept for GetByID", "quality": "Reality"}
    target_concept_data = {"name": "Test Target Concept for GetByID", "quality": "Reality"}

    response_source = await async_client.post("/api/v1/concepts/", json=source_concept_data)
    assert response_source.status_code == 201
    source_id = response_source.json()["elementId"]

    response_target = await async_client.post("/api/v1/concepts/", json=target_concept_data)
    assert response_target.status_code == 201
    target_id = response_target.json()["elementId"]

    # Arrange: Create a relationship
    rel_type = "TEST_GET_BY_ID"
    # Ensure properties match the RelationshipProperties model
    rel_props = {"confidence_score": 0.99} # CHANGED back to confidence_score
    relationship_data = {
        "source_id": source_id,
        "target_id": target_id,
        "type": rel_type,
        "properties": rel_props
    }
    response_create = await async_client.post("/api/v1/relationships/", json=relationship_data)
    assert response_create.status_code == 201
    rel_element_id = response_create.json()["elementId"]
    initial_properties = response_create.json().get("properties", {})

    # Act: Get the relationship by its element ID
    response_get = await async_client.get(f"/api/v1/relationships/{rel_element_id}")

    # Assert
    assert response_get.status_code == 200
    data = response_get.json()
    assert data["elementId"] == rel_element_id
    assert data["type"] == rel_type
    assert data["source_id"] == source_id
    assert data["target_id"] == target_id
    # Ensure the properties dictionary matches the expected structure
    assert "confidence_score" in data["properties"] # CHANGED back to confidence_score
    assert data["properties"]["confidence_score"] == rel_props["confidence_score"] # CHANGED back to confidence_score


@pytest.mark.anyio
async def test_get_relationship_by_id_not_found(async_client: AsyncClient):
    """Test retrieving a non-existent relationship by ID (404)."""
    # Arrange: Choose an ID that is unlikely to exist
    non_existent_id = "5:FakeRelationship:xxxxxxxx"

    # Act
    response = await async_client.get(f"/api/v1/relationships/{non_existent_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- Tests for PATCH /relationships/{element_id} ---

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data", "clear_db_before_test")
async def test_update_relationship_properties_success(async_client: AsyncClient):
    """Test successfully updating properties of a relationship."""
    # Arrange: Create a relationship
    rel_type = "TEST_UPDATE_SUCCESS"
    initial_props = {"confidence_score": 0.5, "distance": 10.0, "spatial_unit": "m"} # CHANGED back to confidence_score
    created_rel = await create_test_relationship(async_client, rel_type, initial_props)
    rel_element_id = created_rel["elementId"]

    # Arrange: Define the update payload
    update_payload = {
        "properties": {
            "confidence_score": 0.95, # CHANGED back to confidence_score
            "distance": None, # Test removing a property by setting to null
            "relation_type": "nearby" # Test adding a new property
        }
    }

    # Act: Update the relationship
    response = await async_client.patch(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}", json=update_payload)

    # Assert Status Code
    assert response.status_code == status.HTTP_200_OK

    # Assert Response Body Structure and Values
    data = response.json()
    assert data["elementId"] == rel_element_id
    assert data["type"] == rel_type
    assert data["source_id"] == created_rel["source_id"]
    assert data["target_id"] == created_rel["target_id"]

    # Assert Updated Properties
    updated_props = data.get("properties", {})
    assert updated_props["confidence_score"] == update_payload["properties"]["confidence_score"] # CHANGED back to confidence_score
    assert "distance" not in updated_props or updated_props["distance"] is None # Check property removed/nullified
    assert "spatial_unit" in updated_props # Ensure other properties remain
    assert updated_props["spatial_unit"] == initial_props["spatial_unit"]
    assert "relation_type" in updated_props # Check new property added
    assert updated_props["relation_type"] == update_payload["properties"]["relation_type"]
    assert "created_at" in updated_props # Ensure timestamp is still there

    # Optional: Verify in DB directly (or via GET)
    get_response = await async_client.get(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}")
    assert get_response.status_code == status.HTTP_200_OK
    get_data = get_response.json()
    get_props = get_data.get("properties", {})
    assert get_props["confidence_score"] == update_payload["properties"]["confidence_score"] # CHANGED back to confidence_score
    assert "distance" not in get_props or get_props["distance"] is None
    assert get_props["relation_type"] == update_payload["properties"]["relation_type"]

@pytest.mark.anyio
async def test_update_relationship_not_found(async_client: AsyncClient):
    """Test attempting to update a non-existent relationship (404)."""
    # Arrange: Choose an ID that is unlikely to exist
    non_existent_id = "5:FakeUpdate:xxxxxxxx"
    update_payload = {"properties": {"confidence_score": 0.1}} # CHANGED back to confidence_score

    # Act
    response = await async_client.patch(f"{RELATIONSHIPS_ENDPOINT}{non_existent_id}", json=update_payload)

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data", "clear_db_before_test")
async def test_update_relationship_invalid_property(async_client: AsyncClient):
    """Test attempting to update with invalid properties (e.g., invalid relation_type for SPATIALLY_RELATES_TO)."""
    # Arrange: Create a SPATIALLY_RELATES_TO relationship with valid initial props
    rel_type = "SPATIALLY_RELATES_TO"
    initial_props = {
        "confidence_score": 0.6, # CHANGED back to confidence_score
        "source_information": "test_invalid_prop", # ADDED source_information
        "distance": 5.0,
        "spatial_unit": "meters", # Use a valid unit recognized by the validator
        "relation_type": "contains", # Valid initial type
        "spatial_dimension": "3D"    # Valid initial dimension
    }
    created_rel = await create_test_relationship(async_client, rel_type, initial_props)
    rel_element_id = created_rel["elementId"]

    # Act: Attempt to update with an invalid 'relation_type'
    invalid_update_payload = {
        "properties": {
            "relation_type": "invalid_spatial_relation" # This should fail validation
        }
    }
    response = await async_client.patch(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}", json=invalid_update_payload)

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    # Optionally, check the detail message for more specific error info
    # detail = response.json().get("detail")
    # assert "invalid_spatial_relation" in detail[0].get("msg", "") # Example check

@pytest.mark.anyio
@pytest.mark.usefixtures("load_sample_data", "clear_db_before_test")
async def test_update_relationship_empty_payload(async_client: AsyncClient):
    """Test updating with an empty payload (should return original data)."""
    # Arrange: Create a relationship
    rel_type = "TEST_EMPTY_UPDATE"
    initial_props = {"confidence_score": 0.8} # CHANGED back to confidence_score
    created_rel = await create_test_relationship(async_client, rel_type, initial_props)
    rel_element_id = created_rel["elementId"]

    # Arrange: Empty payloads
    empty_payload_1 = {}
    empty_payload_2 = {"properties": {}}

    # Act & Assert 1: Completely empty payload
    response1 = await async_client.patch(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}", json=empty_payload_1)
    assert response1.status_code == status.HTTP_400_BAD_REQUEST

    # Act & Assert 2: Payload with empty properties object
    response2 = await async_client.patch(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}", json=empty_payload_2)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST


# ---- DELETE Tests ----

@pytest.mark.anyio
@pytest.mark.usefixtures("clear_db_before_test") # Ensures clean slate
async def test_delete_relationship_success(async_client: AsyncClient):
    """Test successfully deleting an existing relationship."""
    # Arrange: Create a relationship to delete
    rel_type = "TEST_DELETE_SUCCESS"
    created_rel = await create_test_relationship(async_client, rel_type)
    rel_element_id = created_rel["elementId"]
    assert rel_element_id is not None

    # Act: Delete the relationship
    delete_response = await async_client.delete(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}")

    # Assert: Deletion successful
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Assert: Verify relationship is gone by trying to get it
    get_response = await async_client.get(f"{RELATIONSHIPS_ENDPOINT}{rel_element_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.anyio
@pytest.mark.usefixtures("clear_db_before_test")
async def test_delete_relationship_not_found(async_client: AsyncClient):
    """Test attempting to delete a relationship that does not exist."""
    # Arrange: Generate a non-existent element ID
    # Note: The format might be specific, adapt if necessary, but likely any non-matching string works
    non_existent_id = "5:FakeRelationship:1234567890"

    # Act: Attempt to delete the non-existent relationship
    delete_response = await async_client.delete(f"{RELATIONSHIPS_ENDPOINT}{non_existent_id}")

    # Assert: Should return 404 Not Found
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.trio
@pytest.mark.usefixtures("clear_db_before_test")
async def test_delete_relationship_not_found_trio(async_client: AsyncClient):
    """Test attempting to delete a relationship that does not exist."""
    # Arrange: Generate a non-existent element ID
    # Note: The format might be specific, adapt if necessary, but likely any non-matching string works
    non_existent_id = "5:FakeRelationship:1234567890"

    # Act: Attempt to delete the non-existent relationship
    delete_response = await async_client.delete(f"{RELATIONSHIPS_ENDPOINT}{non_existent_id}")

    # Assert: Should return 404 Not Found
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT 