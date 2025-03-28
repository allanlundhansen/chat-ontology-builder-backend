import pytest
from fastapi.testclient import TestClient # Need TestClient if using client fixture indirectly
# No longer need app imported here if using client fixture from conftest
# from src.main import app
# client = TestClient(app) # Remove global client
# Import neo4j session type hint if needed
from neo4j import AsyncSession
import uuid
import traceback
from httpx import AsyncClient # Use AsyncClient if standardizing

@pytest.fixture(scope="function")
# Change fixture input name and type hint
async def test_concepts_for_rels(neo4j_async_session: AsyncSession):
    """
    Fixture to create two temporary concepts directly in the test DB
    using the provided ASYNC session, and return their actual element IDs.
    Includes cleanup.
    """
    # Use unique names
    concept1_data = {"name": f"___TestRelSourceDirect_{uuid.uuid4()}___", "stability": "ephemeral", "confidence": 0.5}
    concept2_data = {"name": f"___TestRelTargetDirect_{uuid.uuid4()}___", "stability": "ephemeral", "confidence": 0.5}
    ids = []
    created_ids = [] # Keep track of successfully created IDs for potential cleanup

    print("\nCreating temporary concepts directly via ASYNC DB session for relationship test...")
    try:
        # Use the async session fixture to run queries
        create_query = """
            CREATE (c:Concept {
                name: $name,
                stability: $stability,
                confidence: $confidence,
                creation_timestamp: datetime(),
                id: randomUUID(),
                description: null,
                quality: null,
                modality: null
            })
            RETURN elementId(c) AS id
        """

        # Use await for async operations
        result1 = await neo4j_async_session.run(create_query, name=concept1_data["name"], stability=concept1_data["stability"], confidence=concept1_data["confidence"])
        record1 = await result1.single(strict=True) # Use await
        concept1_id = record1["id"]
        ids.append(concept1_id)
        created_ids.append(concept1_id) # Track success

        result2 = await neo4j_async_session.run(create_query, name=concept2_data["name"], stability=concept2_data["stability"], confidence=concept2_data["confidence"])
        record2 = await result2.single(strict=True) # Use await
        concept2_id = record2["id"]
        ids.append(concept2_id)
        created_ids.append(concept2_id) # Track success

        print(f"Created temporary concepts directly with element IDs: {ids}")
        yield ids[0], ids[1] # Provide IDs to the test

    except Exception as e:
        print(f"\nError during test_concepts_for_rels fixture setup (direct DB async): {e}")
        traceback.print_exc() # Add traceback for debugging setup errors
        pytest.fail(f"Failed to set up test concepts via direct DB (async): {e}", pytrace=False)

    finally:
        if created_ids:
            print(f"\nCleaning up temporary concepts created by fixture (direct DB async): {created_ids}")
            try:
                # Use await for cleanup query
                await neo4j_async_session.run("MATCH (n) WHERE elementId(n) IN $ids DETACH DELETE n", ids=created_ids)
                print("Temporary concepts cleanup successful.")
            except Exception as e:
                print(f"WARN: Failed to cleanup temporary concepts in fixture (async): {e}")


# --- Updated Tests using Fixtures ---

def test_create_concept_invalid_quality(client): # Use client fixture
    """
    Test that creating a concept with invalid 'quality' fails
    and the KantianValidationError handler returns the correct 422 response.
    """
    invalid_concept_data = {
        "name": "Test Concept Invalid Quality",
        "quality": "NonExistentQuality", # This should fail KantianValidator
        "modality": None,
        "description": "Test desc" # Assuming description might be needed
    }
    response = client.post("/api/v1/concepts/", json=invalid_concept_data)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    assert len(error_detail) == 1
    assert error_detail[0]["loc"] == ["body", "quality"]
    assert "Invalid Quality" in error_detail[0]["msg"]
    assert error_detail[0]["type"] == "kantian_validation_error"

@pytest.mark.asyncio
async def test_create_relationship_missing_spatial_unit(client, test_concepts_for_rels):
    """
    Test spatial relationship validation using temporary concepts created by fixture.
    """
    concept1_id, concept2_id = test_concepts_for_rels # Get actual element IDs from fixture
    invalid_rel_data = {
        "type": "SPATIALLY_RELATES_TO",
        "source_id": concept1_id, # Use actual ID
        "target_id": concept2_id, # Use actual ID
        "properties": {
            "distance": 10, # Missing spatial_unit
            "confidence": 0.9
        }
    }
    response = client.post("/api/v1/relationships/", json=invalid_rel_data)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    assert len(error_detail) == 1
    assert error_detail[0]["loc"][-1] == "spatial_unit" # Check the field name
    assert error_detail[0]["msg"] == "Spatial relationships require 'spatial_unit' when 'distance' is present"
    assert error_detail[0]["type"] == "kantian_validation_error"

def test_pydantic_validation_error(client): # Use client fixture
    """
    Test that a request missing a required Pydantic field (e.g., name)
    triggers the RequestValidationError handler correctly.
    """
    incomplete_concept_data = {
        # Missing 'name'
        "quality": "Reality",
        "description": "Test desc" # Assuming description might be needed
    }
    response = client.post("/api/v1/concepts/", json=incomplete_concept_data)
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    # Check for an error related to the 'name' field being missing
    assert any(
        err["loc"] == ["body", "name"] and "missing" in err["type"].lower()
        for err in error_detail
    ), f"Expected 'name' missing error, got: {error_detail}"

# --- NEW Test Cases ---

def test_create_concept_invalid_modality(client):
    """
    Test creating a concept with an invalid 'modality' value fails
    and the KantianValidationError handler returns the correct 422 response.
    """
    invalid_concept_data = {
        "name": "Test Concept Invalid Modality",
        "quality": "Reality",
        "modality": "MaybePerhapsPossibly", # Invalid modality value
        "description": "Test desc"
    }
    response = client.post("/api/v1/concepts/", json=invalid_concept_data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"

    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    assert len(error_detail) == 1, f"Expected 1 error detail, got {len(error_detail)}"
    # Check location, message, and type for modality error
    assert error_detail[0]["loc"] == ["body", "modality"], f"Expected loc ['body', 'modality'], got {error_detail[0]['loc']}"
    assert "Invalid Modality" in error_detail[0]["msg"], f"Expected 'Invalid Modality' in msg, got {error_detail[0]['msg']}"
    assert error_detail[0]["type"] == "kantian_validation_error", f"Expected type 'kantian_validation_error', got {error_detail[0]['type']}"


@pytest.mark.asyncio
async def test_create_relationship_invalid_spatial_unit(client, test_concepts_for_rels):
    """
    Test creating a spatial relationship with an invalid 'spatial_unit' value
    fails and the KantianValidationError handler returns the correct 422 response.
    """
    concept1_id, concept2_id = test_concepts_for_rels # Get actual element IDs

    invalid_rel_data = {
        "type": "SPATIALLY_RELATES_TO",
        "source_id": concept1_id,
        "target_id": concept2_id,
        "properties": {
            "distance": 50,
            "spatial_unit": "furlongs", # Invalid unit based on VALID_SPATIAL_UNITS
            "confidence": 0.8
        }
    }
    response = client.post("/api/v1/relationships/", json=invalid_rel_data)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}. Response: {response.text}"

    error_detail = response.json()["detail"]
    assert isinstance(error_detail, list)
    assert len(error_detail) == 1, f"Expected 1 error detail, got {len(error_detail)}"
    # Adjust the check for the error location if needed based on the actual response
    assert error_detail[0]["loc"][-1] == "spatial_unit" # Check the field name
    # Check the specific error message from the validator
    assert "Invalid spatial_unit" in error_detail[0]["msg"]
    assert "furlongs" in error_detail[0]["msg"]
    # --- Ensure type matches handler ---
    assert error_detail[0]["type"] == "kantian_validation_error"

# --- TODO: Add more test cases for other validation rules --- 