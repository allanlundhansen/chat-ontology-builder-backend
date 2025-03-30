import sys
import os

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
PROJECT_ROOT = project_root

import pytest
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, GraphDatabase, Driver, Session, AsyncTransaction
import pytest_asyncio
from typing import AsyncGenerator, Optional, AsyncIterator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
# Make sure anyio is installed (it should be a dependency of httpx)
# import anyio

# --- App and Original Driver Import ---
from src.main import app as application
# Keep import for the dependency we need to OVERRIDE
from src.db.neo4j_driver import get_db
# Import setup functions
from scripts.setup_database import clear_database, run_setup_scripts

# --- Load .env file ---
dotenv_path = os.path.join(PROJECT_ROOT, '.env')
print(f"Attempting to load .env file from: {dotenv_path}")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(".env file loaded.")
else:
    print("Warning: .env file not found, relying solely on environment variables.")
# -----------------------------------------------

# --- Constants ---
# Use the standard default database name for Neo4j
DEFAULT_DB_NAME = "neo4j"

# --- Get Test DB Credentials ---
NEO4J_TEST_URI = os.getenv("NEO4J_TEST_URI")
NEO4J_TEST_USER = os.getenv("NEO4J_TEST_USER")
NEO4J_TEST_PASSWORD = os.getenv("NEO4J_TEST_PASSWORD")
# Define the database name to use for tests (can also be from .env if needed)
DEFAULT_DB_NAME = os.getenv("NEO4J_TEST_DATABASE", "neo4j")
# --- End Test DB Credentials ---

# Global variable to hold the driver instance for the test session
_test_driver: Driver | None = None

def get_neo4j_test_driver() -> Driver:
    """Initializes and returns a Neo4j Driver instance for the TEST database."""
    global _test_driver
    if _test_driver is None:
        uri = os.getenv("NEO4J_TEST_URI")
        user = os.getenv("NEO4J_TEST_USER")
        password = os.getenv("NEO4J_TEST_PASSWORD")
        if not uri or not user or not password:
            pytest.fail("Missing Neo4j Test DB credentials in .env file (NEO4J_TEST_URI, NEO4J_TEST_USER, NEO4J_TEST_PASSWORD)", pytrace=False)

        try:
            print(f"\nAttempting to connect to Neo4j Test DB: {uri}")
            _test_driver = GraphDatabase.driver(uri, auth=(user, password))
            _test_driver.verify_connectivity()
            print("Successfully connected to Neo4j Test DB.")
        except Exception as e:
            pytest.fail(f"Failed to connect or verify connectivity to Neo4j Test DB: {e}", pytrace=False)

    return _test_driver

@pytest.fixture(scope="session", autouse=True)
def manage_neo4j_driver(request):
    """Pytest fixture to initialize and close the Neo4j driver for the test session."""
    driver = get_neo4j_test_driver() # Ensure driver is initialized
    yield # Run tests
    global _test_driver
    if _test_driver:
        print("\nClosing Neo4j Test DB driver.")
        _test_driver.close()
        _test_driver = None

@pytest_asyncio.fixture(scope="function")
async def neo4j_async_session(async_test_driver: AsyncDriver) -> AsyncGenerator[AsyncTransaction, None]:
    """
    Provides an async transaction that rolls back after the test.
    The session is managed internally.
    Scope: function
    """
    print(f"\nDEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Acquiring session for DB \'{DEFAULT_DB_NAME}\'...")
    session: AsyncSession | None = None
    tx: AsyncTransaction | None = None
    try:
        session = async_test_driver.session(database=DEFAULT_DB_NAME)
        tx = await session.begin_transaction()
        print("DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Began transaction, yielding transaction...")
        yield tx # Yield the transaction object
    finally:
        if tx: # No need to check tx.open, rollback is idempotent
            try:
                if tx.is_open(): # Use internal method if available, otherwise just try rollback
                    print("DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Rolling back open transaction...")
                    await tx.rollback()
                    print("DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Transaction rolled back.")
                else:
                    print("DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Transaction already closed/rolled back.")
            except Exception as e: # Catch potential errors if rollback fails unexpectedly
                print(f"WARN [conftest - neo4j_async_session]: Error during rollback check/attempt: {e}")
                # Still ensure session is closed below
        else:
            print("DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: No transaction object to roll back.")

        if session:
             await session.close()
             print(f"DEBUG [conftest - neo4j_async_session - FUNCTION SCOPE]: Session for DB \'{DEFAULT_DB_NAME}\' closed.")

@pytest.fixture(scope="function")
def client(app: FastAPI): # Add type hint for app fixture if not already present
    """
    Provides a FastAPI TestClient instance with explicit asyncio backend.
    """
    # Use a context manager to ensure lifespan events (startup/shutdown) are run
    # Explicitly set the backend to 'asyncio'
    with TestClient(app, backend="asyncio") as test_client:
        yield test_client

# --- Fixtures ---

@pytest_asyncio.fixture(scope="session")
async def async_test_driver() -> AsyncGenerator[AsyncDriver, None]:
    """
    ASYNC: Provides a Neo4j AsyncDriver instance FOR TESTS, using test credentials.
    Handles setup and teardown of the driver connection.
    Scope: session
    """
    print("\nDEBUG [conftest - async_test_driver - SESSION SCOPE]: Setting up TEST async driver...")
    if not NEO4J_TEST_URI or not NEO4J_TEST_USER or not NEO4J_TEST_PASSWORD:
        pytest.fail(
            "Neo4j TEST connection details (NEO4J_TEST_URI, NEO4J_TEST_USER, NEO4J_TEST_PASSWORD) "
            "not found in environment variables. Ensure .env is loaded and variables are set."
        )

    driver: Optional[AsyncDriver] = None
    try:
        # Create the driver directly using TEST credentials
        driver = AsyncGraphDatabase.driver(
            NEO4J_TEST_URI,
            auth=(NEO4J_TEST_USER, NEO4J_TEST_PASSWORD)
        )
        await driver.verify_connectivity()
        print(f"DEBUG [conftest - async_test_driver - SESSION SCOPE]: TEST Async driver connected to {NEO4J_TEST_URI}.")
        yield driver # Yield the test driver instance
    except Exception as e:
        import traceback
        traceback.print_exc()
        pytest.fail(f"Failed to initialize TEST async Neo4j driver: {e}")
    finally:
        if driver:
            print("DEBUG [conftest - async_test_driver - SESSION SCOPE]: Closing TEST async driver...")
            await driver.close()
            print("DEBUG [conftest - async_test_driver - SESSION SCOPE]: TEST Async driver closed.")
        else:
             print("DEBUG [conftest - async_test_driver - SESSION SCOPE]: No TEST async driver to close.")

# Changed scope to "session" to align with client
@pytest.fixture(scope="session")
def app() -> FastAPI:
    """
    Provides the FastAPI application instance for the test session.
    Scope: session
    """
    print("\nDEBUG [conftest - app - SESSION SCOPE]: Providing FastAPI app instance.") # Update log scope
    yield application # Yield the imported app instance

@pytest_asyncio.fixture(scope="session", autouse=True)
async def manage_db_state(async_test_driver: AsyncDriver):
    """
    ASYNC: Clears the test database BEFORE the test session starts. (Session Scope)
    Uses the session-scoped async_test_driver connected to the TEST DB.
    """
    print(f"\nDEBUG [conftest - manage_db_state - SESSION SCOPE]: Clearing TEST DB '{DEFAULT_DB_NAME}' at start of session.")
    try:
        # Pass the correct database name
        await clear_database(async_test_driver, DEFAULT_DB_NAME)
        print(f"DEBUG [conftest - manage_db_state - SESSION SCOPE]: TEST DB '{DEFAULT_DB_NAME}' cleared.")
        yield # Yield control to tests for the session
    except Exception as e:
        pytest.fail(f"Failed to clear TEST database '{DEFAULT_DB_NAME}' at session start: {e}")

@pytest_asyncio.fixture(scope="session", autouse=True)
async def load_sample_data(manage_db_state, async_test_driver: AsyncDriver):
    """
    ASYNC: Loads sample data AFTER clearing the TEST DB. Runs once per session. (Session Scope)
    Depends on manage_db_state (for order) and async_test_driver (for the TEST driver instance).
    """
    print(f"\nDEBUG [conftest - load_sample_data - SESSION SCOPE]: Loading sample data into TEST DB '{DEFAULT_DB_NAME}'...")
    try:
        # Pass the correct database name
        await run_setup_scripts(async_test_driver, DEFAULT_DB_NAME, include_samples=True)
        print(f"DEBUG [conftest - load_sample_data - SESSION SCOPE]: Sample data loaded into TEST DB '{DEFAULT_DB_NAME}'.")
        yield # Yield control for the duration of the session
    except Exception as e:
        pytest.fail(f"Failed to load sample data into TEST DB '{DEFAULT_DB_NAME}' at session start: {e}")
    finally:
        print(f"DEBUG [conftest - load_sample_data - SESSION SCOPE]: Teardown (if any) for TEST DB '{DEFAULT_DB_NAME}'.")

# CORRECTED: Scope changed to "function"
@pytest_asyncio.fixture(scope="function")
# CORRECTED: Depend on the actual fixture name 'neo4j_async_session'
async def async_client(app: FastAPI, neo4j_async_session: AsyncTransaction) -> AsyncGenerator[AsyncClient, None]:
    """
    ASYNC: Provides an HTTPX AsyncClient for making requests directly to the test app ASGI interface.
    Overrides the application's database dependency (get_db) to use the function-scoped transaction object.
    Scope: function
    """
    print("\nDEBUG [conftest - async_client - FUNCTION SCOPE]: Setting up async test client...")

    # Define the override function *inside* the fixture so it closes over the injected transaction
    async def override_get_db_for_test() -> AsyncGenerator[AsyncTransaction, None]: # Changed return type
        print(f"DEBUG [conftest - override_get_db_for_test]: Yielding transaction object from neo4j_async_session fixture.")
        # Yield the already-existing transaction object from the function-scoped fixture
        yield neo4j_async_session # Yield the tx
        # No need to close or manage transaction here, neo4j_async_session handles it

    # Apply the override for this specific test function's scope
    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db_for_test
    print("DEBUG [conftest - async_client - FUNCTION SCOPE]: Dependency override set for function.")

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
            print("DEBUG [conftest - async_client - FUNCTION SCOPE]: Yielding async test client (following redirects).")
            yield client
            print("DEBUG [conftest - async_client - FUNCTION SCOPE]: Async test client scope exiting.")
    finally:
        # Restore the original override (or remove if none existed)
        print("DEBUG [conftest - async_client - FUNCTION SCOPE]: Removing/Restoring dependency override for function.")
        if original_override:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)
        print("DEBUG [conftest - async_client - FUNCTION SCOPE]: Finished function scope cleanup.")

# NEW Fixture: Clears DB before specific tests (function scope)
@pytest_asyncio.fixture(scope="function")
async def clear_db_before_test(async_test_driver: AsyncDriver):
    """
    ASYNC: Clears the test database BEFORE a specific test function runs. (Function Scope)
    Use this for tests that require a completely empty state.
    """
    print(f"\nDEBUG [conftest - clear_db_before_test - FUNCTION SCOPE]: Clearing TEST DB '{DEFAULT_DB_NAME}' before test function.")
    try:
        # Pass the correct database name
        await clear_database(async_test_driver, DEFAULT_DB_NAME)
        print(f"DEBUG [conftest - clear_db_before_test - FUNCTION SCOPE]: TEST DB '{DEFAULT_DB_NAME}' cleared for test.")
        # No yield needed for a simple setup fixture like this
    except Exception as e:
        pytest.fail(f"Failed to clear TEST database '{DEFAULT_DB_NAME}' before test function: {e}")

# --- Optional: Helper for Python < 3.10 if needed ---
# async def anext(ait: AsyncIterator):
#     """Helper for getting the next item from an async iterator for Python < 3.10"""
#     return await ait.__anext__()
# If you are using Python 3.10+, you don't need this helper. 