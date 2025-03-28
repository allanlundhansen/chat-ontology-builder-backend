import os
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession, exceptions as neo4j_exceptions # Import Async types and exceptions
from dotenv import load_dotenv
from typing import Optional, AsyncGenerator # Added typing
import traceback # Add traceback import
from contextlib import asynccontextmanager
from fastapi import HTTPException, status

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
    Handles session acquisition errors, lets endpoint errors propagate.
    Ensures session is closed even if endpoint raises an error.
    """
    main_driver: Optional[AsyncDriver] = None
    session: Optional[AsyncSession] = None
    try:
        main_driver = await get_async_driver()
        # Use the database specified in env or default
        db_name = NEO4J_DATABASE # Use the global/env var consistently
        print(f"DEBUG: Attempting to acquire session for database '{db_name}'...")
        session = main_driver.session(database=db_name)
        print(f"DEBUG: Acquired session: {session}")
        yield session # Provide session to the endpoint

    except (neo4j_exceptions.ServiceUnavailable, neo4j_exceptions.AuthError, RuntimeError) as e:
        # Catch specific driver/connection/init errors
        print(f"ERROR: Failed to acquire DB session dependency: {type(e).__name__}: {e}")
        # Raise HTTPException so FastAPI handles it, preventing endpoint execution
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not get database session: {e}"
        ) from e
    finally:
        # This block executes whether the 'yield' completes or raises an exception
        if session:
            try:
                await session.close()
                print("DEBUG: Neo4j session closed by get_db finally block.")
            except Exception as close_err:
                # Log error but don't overshadow original exception if one occurred
                print(f"WARN: Failed to close session cleanly in get_db finally: {close_err}")
        else:
             print("DEBUG: No session to close in get_db finally block.")

# Note: The test environment uses its own driver instance created in conftest.py
# This file now correctly provides the async driver and `get_db` dependency for the main app.
