import os
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession # Import Async types
from dotenv import load_dotenv
from typing import Optional, AsyncGenerator # Added typing
import traceback # Add traceback import

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687") # Use the non-test URI for the app
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j") # App's default database

# Use Optional[AsyncDriver] for the global driver variable
_driver: Optional[AsyncDriver] = None

async def get_async_driver() -> AsyncDriver:
    """
    Initializes and returns the Neo4j AsyncDriver instance for the application.
    Uses singleton pattern to reuse the driver. Connects to the main application DB (not test DB).
    """
    global _driver
    print("DEBUG: Entering get_async_driver") # ADDED
    if _driver is None:
        print("DEBUG: _driver is None, attempting to create main driver.") # ADDED
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            print("ERROR: Missing main Neo4j connection details in env.") # ADDED
            raise ValueError("Neo4j connection details (URI, USERNAME, PASSWORD) not found in environment variables.")
        try:
            print(f"DEBUG: Attempting AsyncGraphDatabase.driver connect to {NEO4J_URI}") # ADDED
            _driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            print(f"DEBUG: Driver object created: {_driver}") # ADDED
            print("DEBUG: Attempting driver.verify_connectivity()") # ADDED
            await _driver.verify_connectivity()
            print("DEBUG: Successfully verified connectivity for main driver.") # ADDED
        except Exception as e:
            print(f"ERROR in get_async_driver during connection/verification: {type(e).__name__}: {e}") # ADDED
            traceback.print_exc() # ADDED - Print original traceback
            raise # Re-raise the original connection error
    else:
        print("DEBUG: Reusing existing main _driver instance.") # ADDED
    # Ensure driver is not None before returning
    if _driver is None:
         raise RuntimeError("Failed to initialize main Neo4j async driver.") # Should not happen if connect works
    print("DEBUG: Returning main driver instance.") # ADDED
    return _driver

async def close_async_driver():
    """Closes the main application's Neo4j AsyncDriver connection if it exists."""
    global _driver
    if _driver is not None:
        print("Closing main Neo4j async driver...")
        await _driver.close() # Use await for async close
        _driver = None
        print("Main Neo4j async driver closed.")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injector that yields an AsyncSession using the main application driver.
    """
    print("DEBUG: Entering get_db dependency") # ADDED
    global NEO4J_DATABASE
    main_driver: Optional[AsyncDriver] = None # Initialize as Optional
    try:
        print("DEBUG: Calling await get_async_driver()") # ADDED
        main_driver = await get_async_driver()
        print(f"DEBUG: Got main_driver: {main_driver}") # ADDED
        # Use the database specified in env or default for the application
        print(f"DEBUG: Attempting 'async with main_driver.session(database={NEO4J_DATABASE})'") # ADDED
        async with main_driver.session(database=NEO4J_DATABASE) as session:
            print(f"DEBUG: Acquired session: {session}") # ADDED
            yield session
            print("DEBUG: Yielded session scope finished.") # ADDED
    except Exception as e:
        print(f"ERROR caught in get_db: {type(e).__name__}: {e}") # Log type and message of original error
        traceback.print_exc() # ADDED - Print original traceback here too
        # Raising RuntimeError as before, but now we have better logs
        raise RuntimeError(f"Could not get database session from main driver: {e}") from e
    finally:
        # This block might not be reached if yield fails, but good practice
        print(f"DEBUG: get_db dependency finished (session automatically closed by 'async with').")

# Note: The test environment uses its own driver instance created in conftest.py
# This file now correctly provides the async driver and `get_db` dependency for the main app.
