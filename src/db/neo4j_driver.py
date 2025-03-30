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
    if _driver is None:
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            raise ValueError("Missing Neo4j connection details in environment variables.")
        try:
            _driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            await _driver.verify_connectivity()
        except Exception as e:
            _driver = None
            raise HTTPException(status_code=503, detail="Could not connect to the database.") from e
    else:
        pass
    return _driver

async def close_async_driver():
    """Closes the main application's Neo4j AsyncDriver connection if it exists."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None

async def get_db(db_name: str = NEO4J_DATABASE) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injector that yields an AsyncSession using the main application driver.
    Handles session acquisition errors, lets endpoint errors propagate.
    Ensures session is closed even if endpoint raises an error.
    """
    driver: Optional[AsyncDriver] = None
    session: Optional[AsyncSession] = None
    try:
        driver = await get_async_driver()
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
