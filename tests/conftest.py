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
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, GraphDatabase, Driver, Session
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
async def neo4j_async_session(async_test_driver: AsyncDriver) -> AsyncGenerator[AsyncSession, None]:
    """Provides an async session to the test database."""
    print("\n--- Creating Async Test Session (Function Scope) ---")
    async with async_test_driver.session(database=DEFAULT_DB_NAME) as session:
        yield session
    print("--- Closed Async Test Session (Function Scope) ---")

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

# Keep session scope (as decided previously)
@pytest_asyncio.fixture(scope="session")
async def async_client(app: FastAPI, async_test_driver: AsyncDriver) -> AsyncGenerator[AsyncClient, None]:
    """
    ASYNC: Provides an HTTPX AsyncClient for making requests directly to the test app ASGI interface.
    Overrides the application's database dependency (get_db) ONCE for the session.
    Scope: session
    """
    print("\nDEBUG [conftest - async_client - SESSION SCOPE]: Setting up async test client...")

    async def override_get_db_for_test() -> AsyncGenerator[AsyncSession, None]:
        print(f"DEBUG [conftest - override_get_db_for_test]: Acquiring session from TEST driver for DB '{DEFAULT_DB_NAME}'...")
        async with async_test_driver.session(database=DEFAULT_DB_NAME) as session:
            print("DEBUG [conftest - override_get_db_for_test]: Yielding session...")
            yield session
            print("DEBUG [conftest - override_get_db_for_test]: Session scope exiting.")

    app.dependency_overrides[get_db] = override_get_db_for_test
    print("DEBUG [conftest - async_client - SESSION SCOPE]: Dependency override set.")

    transport = ASGITransport(app=app)
    # Pass the transport AND add follow_redirects=True
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        print("DEBUG [conftest - async_client - SESSION SCOPE]: Yielding async test client (following redirects).")
        yield client
        print("DEBUG [conftest - async_client - SESSION SCOPE]: Async test client scope exiting.")

    print("DEBUG [conftest - async_client - SESSION SCOPE]: Removing dependency override.")
    app.dependency_overrides.pop(get_db, None)
    print("DEBUG [conftest - async_client - SESSION SCOPE]: Finished session scope cleanup.")

# --- Optional: Helper for Python < 3.10 if needed ---
# async def anext(ait: AsyncIterator):
#     """Helper for getting the next item from an async iterator for Python < 3.10"""
#     return await ait.__anext__()
# If you are using Python 3.10+, you don't need this helper. 