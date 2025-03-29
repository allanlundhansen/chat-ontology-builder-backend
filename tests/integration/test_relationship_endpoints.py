import pytest
from httpx import AsyncClient
from fastapi import status
from typing import List, Dict, Any
import asyncio # Import asyncio for sleep

# Define the base endpoint path
RELATIONSHIPS_ENDPOINT = "/api/v1/relationships/"
CONCEPTS_ENDPOINT = "/api/v1/concepts/" # Needed to create nodes

# Helper function to create concepts and relationships for tests
async def create_test_relationship(async_client: AsyncClient, rel_type: str, properties: Dict = None) -> Dict[str, Any]:
    """Creates two concepts and a relationship between them."""
    # Create source concept
    prop_id_str = f"_{properties.get('id')}" if properties and 'id' in properties else ""
    source_concept_data = {"name": f"Source_{rel_type}{prop_id_str}"}
    source_res = await async_client.post(CONCEPTS_ENDPOINT, json=source_concept_data)
    assert source_res.status_code == status.HTTP_201_CREATED
    source_id = source_res.json().get("elementId")
    assert source_id

    # Create target concept
    target_concept_data = {"name": f"Target_{rel_type}{prop_id_str}"}
    target_res = await async_client.post(CONCEPTS_ENDPOINT, json=target_concept_data)
    assert target_res.status_code == status.HTTP_201_CREATED
    target_id = target_res.json().get("elementId")
    assert target_id

    # Create relationship
    rel_data = {
        "type": rel_type,
        "source_id": source_id,
        "target_id": target_id,
        "properties": properties or {"confidence": 0.7} # Default properties if none provided
    }
    rel_res = await async_client.post(RELATIONSHIPS_ENDPOINT, json=rel_data)
    assert rel_res.status_code == status.HTTP_201_CREATED # Assuming POST relationships returns 201
    created_rel = rel_res.json()
    # Add node IDs for convenience in tests, although they aren't part of POST response
    created_rel['start_node_id'] = source_id
    created_rel['end_node_id'] = target_id
    return created_rel


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
    assert isinstance(data, list)
    # Check if list is not empty (assuming test DB wasn't empty or creation worked)
    if data:
        item = data[0]
        assert "elementId" in item
        assert "type" in item
        assert "start_node_id" in item
        assert "end_node_id" in item
        assert "confidence" in item # Example property check


@pytest.mark.anyio
@pytest.mark.usefixtures("manage_db_state")
async def test_list_relationships_pagination(async_client: AsyncClient):
    """Test pagination (skip, limit) for listing relationships."""
    # Arrange: Create more relationships than default limit (e.g., 12)
    all_rel_ids = set()
    for i in range(12):
        rel = await create_test_relationship(async_client, "TEST_PAGINATION", {"id": i})
        all_rel_ids.add(rel.get("elementId"))
    assert len(all_rel_ids) == 12 # Ensure 12 unique relationships created

    # Act: Get first 5
    max_retries = 3
    retry_delay = 0.3 # seconds

    for attempt in range(max_retries):
        response_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"limit": 5})
        assert response_limit5.status_code == status.HTTP_200_OK
        data_limit5 = response_limit5.json()
        assert isinstance(data_limit5, list)
        if len(data_limit5) == 5:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get 5 relationships after {max_retries} attempts. Got {len(data_limit5)}.")

    # Act: Get next 5 (skip 5)
    for attempt in range(max_retries):
        response_skip5_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"skip": 5, "limit": 5})
        assert response_skip5_limit5.status_code == status.HTTP_200_OK
        data_skip5_limit5 = response_skip5_limit5.json()
        assert isinstance(data_skip5_limit5, list)
        if len(data_skip5_limit5) == 5:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get next 5 relationships (skip 5) after {max_retries} attempts. Got {len(data_skip5_limit5)}.")

    # Act: Get last 2 (skip 10)
    for attempt in range(max_retries):
        response_skip10_limit5 = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"skip": 10, "limit": 5})
        assert response_skip10_limit5.status_code == status.HTTP_200_OK
        data_skip10_limit5 = response_skip10_limit5.json()
        assert isinstance(data_skip10_limit5, list)
        # Expecting the remaining 2
        if len(data_skip10_limit5) == 2:
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get last 2 relationships (skip 10) after {max_retries} attempts. Got {len(data_skip10_limit5)}.")

    # Assert
    assert response_limit5.status_code == status.HTTP_200_OK
    data_limit5 = response_limit5.json()
    assert isinstance(data_limit5, list)
    assert len(data_limit5) == 5

    assert response_skip5_limit5.status_code == status.HTTP_200_OK
    data_skip5_limit5 = response_skip5_limit5.json()
    assert isinstance(data_skip5_limit5, list)
    assert len(data_skip5_limit5) == 5

    assert response_skip10_limit5.status_code == status.HTTP_200_OK
    data_skip10_limit5 = response_skip10_limit5.json()
    assert isinstance(data_skip10_limit5, list)
    assert len(data_skip10_limit5) == 2 # Only 2 remaining

    # Ensure no overlap between pages
    ids_limit5 = {item.get("elementId") for item in data_limit5}
    ids_skip5_limit5 = {item.get("elementId") for item in data_skip5_limit5}
    ids_skip10_limit5 = {item.get("elementId") for item in data_skip10_limit5}

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
        assert isinstance(data, list)
        if len(data) >= 2: # Check if we found at least 2 TYPE_A relationships
            break # Success
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay)
    else: # Loop finished without break
        pytest.fail(f"Failed to get >= 2 relationships of TYPE_A after {max_retries} attempts. Got {len(data)}.")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # Should find at least the two we created
    found_correct_type = False
    found_other_type = False
    for item in data:
        assert "type" in item
        if item["type"] == "TYPE_A":
            found_correct_type = True
        else:
            found_other_type = True # Should not happen
        assert "elementId" in item

    assert found_correct_type is True
    assert found_other_type is False # Ensure ONLY TYPE_A was returned 


@pytest.mark.anyio
@pytest.mark.usefixtures("manage_db_state")
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
    assert isinstance(data, list)
    assert len(data) == 0

    # Act: Request relationships with a filter that won't match anything
    response_filtered = await async_client.get(RELATIONSHIPS_ENDPOINT, params={"type": "NON_EXISTENT_TYPE"})

    # Assert: Expect 200 OK and an empty list
    assert response_filtered.status_code == status.HTTP_200_OK
    data_filtered = response_filtered.json()
    assert isinstance(data_filtered, list)
    assert len(data_filtered) == 0 