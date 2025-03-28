import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver, AsyncDriver, AsyncSession, exceptions as neo4j_exceptions
import time
import asyncio
import re # Import regex for parsing
from typing import List

# Import the statement lists from the new location
try:
    from .cypher_statements import category_structure_statements
    from .cypher_statements import concept_structure_statements
    from .cypher_statements import sample_concept_statements
    # Import relationship statements if you create a file for it
    # from .cypher_statements import relationship_structure_statements
except ImportError as e:
    print(f"[ERROR] Could not import statement modules from .cypher_statements: {e}")
    print("Ensure the directory 'scripts/cypher_statements' exists and contains __init__.py and the statement files.")
    sys.exit(1)


# --- Configuration ---
# Load environment variables from a .env file if it exists
load_dotenv()

# Neo4j Connection Details
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687") # Changed default to bolt
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j") # Default database name

# --- Root Path (to find schema/query files relative to script location) ---
# Assuming setup_database.py is in /scripts, we need to go up one level
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Go up one level from /scripts to project root
RELATIONSHIP_TYPES_PATH = os.path.join(PROJECT_ROOT, "src", "understanding", "schema", "relationship_types.cypher")
# QUERY_TEMPLATES_PATH = os.path.join(PROJECT_ROOT, "src", "understanding", "queries", "query_templates.cypher") # REMOVE or COMMENT OUT


# --- Helper Functions ---

def get_driver() -> Driver:
    """Establishes connection to the Neo4j database."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")
        return driver
    except neo4j_exceptions.AuthError as e:
        print(f"[ERROR] Neo4j authentication failed: {e}")
        sys.exit(1)
    except neo4j_exceptions.ServiceUnavailable as e:
        print(f"[ERROR] Neo4j service unavailable at {NEO4J_URI}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")
        sys.exit(1)


async def clear_database(driver: AsyncDriver, database_name: str):
    """ASYNC: Drops all constraints and deletes all nodes and relationships."""
    print(f"ASYNC Clearing database: {database_name}...")
    try:
        async with driver.session(database=database_name) as session:
            # Define an async transaction function
            async def delete_all(tx):
                result = await tx.run("MATCH (n) DETACH DELETE n")
                await result.consume() # Await consume() on the result

            summary = await session.execute_write(delete_all) # Pass the async function

            # Optionally, add constraint dropping logic here if needed,
            # ensuring you handle potential errors if constraints don't exist.
            # Example (needs refinement based on specific constraints):
            # async def drop_constraints(tx):
            #     constraints = await tx.run("SHOW CONSTRAINTS YIELD name")
            #     async for record in constraints:
            #         await tx.run(f"DROP CONSTRAINT {record['name']}")
            # await session.execute_write(drop_constraints)

            print(f"  ASYNC Database '{database_name}' cleared. Summary: {summary}")

    except Exception as e:
        print(f"  [ERROR] ASYNC Unexpected error during clearing: {e}")
        # Re-raise or handle as appropriate for your testing strategy
        raise e

async def execute_cypher_statements(
    driver: AsyncDriver,
    statements: list[str],
    group_name: str,
    database_name: str = NEO4J_DATABASE,
):
    """ASYNC Executes a list of Cypher statements within a transaction."""
    print(f"ASYNC Attempting to execute statements for: {group_name} in DB '{database_name}'...")
    if not statements:
        print("  No statements provided.")
        return

    statements_to_run = [s.strip() for s in statements if s.strip()]
    if not statements_to_run:
        print("  No non-empty statements to execute.")
        return

    print(f"  ASYNC Found {len(statements_to_run)} statements to execute.")
    async with driver.session(database=database_name) as session:
        count = 0
        try:
            for stmt in statements_to_run:
                count += 1

                # Define an async transaction function for the single statement
                async def run_single_statement(tx, statement_to_run):
                    result = await tx.run(statement_to_run)
                    await result.consume() # Await consume here

                # Pass the async function and the statement to execute_write
                # We need to use functools.partial or a lambda to pass the stmt
                # This lambda creates the async function with the current stmt baked in
                tx_func = lambda tx: run_single_statement(tx, stmt)
                summary = await session.execute_write(tx_func)

                # Optional: Log summary if needed, might be None
                # print(f"    Statement {count} executed. Summary: {summary}")

            print(f"  ASYNC Successfully executed all {count} statements for {group_name}.")

        except Exception as e:
            print(f"  [ERROR] ASYNC Unexpected error executing statement {count} for {group_name}: {e}")
            # Optionally print the failing statement for debugging
            # print(f"    Failing statement: {stmt}")
            raise e # Re-raise unexpected errors


# --- NEW Helper Function to Parse Cypher Files ---
def parse_cypher_file(file_path: str) -> List[str]:
    """Reads a Cypher file and splits it into individual statements."""
    statements = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            # Remove block comments first (/* ... */)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Split by semicolon, the typical statement terminator
            raw_statements = content.split(';')
            for stmt in raw_statements:
                # Remove line comments (// ...)
                stmt_lines = [line for line in stmt.splitlines() if not line.strip().startswith('//')]
                cleaned_stmt = ' '.join(stmt_lines).strip()
                if cleaned_stmt: # Only add non-empty statements
                    statements.append(cleaned_stmt)
        print(f"INFO: Parsed {len(statements)} statements from {os.path.basename(file_path)}")
        return statements
    except FileNotFoundError:
        print(f"[ERROR] Cypher file not found: {file_path}")
        return [] # Return empty list if file not found
    except Exception as e:
        print(f"[ERROR] Failed to parse Cypher file {file_path}: {e}")
        return []


# --- Modified run_setup_scripts Function ---
async def run_setup_scripts(driver: AsyncDriver, database_name: str, include_samples: bool = True):
    """ASYNC: Runs the necessary setup statements from files and modules."""

    # Load statements from files first
    relationship_constraints = parse_cypher_file(RELATIONSHIP_TYPES_PATH)
    # apoc_procedures = parse_cypher_file(QUERY_TEMPLATES_PATH) # REMOVE or COMMENT OUT

    # Load statements from modules
    try:
        # Using getattr for safety
        constraints_statements = getattr(concept_structure_statements, 'CONSTRAINTS_STATEMENTS', [])
        category_statements = getattr(category_structure_statements, 'STATEMENTS', [])
        concept_structure = getattr(concept_structure_statements, 'STATEMENTS', [])
        sample_concepts = getattr(sample_concept_statements, 'STATEMENTS', []) if include_samples else []
    except NameError as e:
        print(f"[ERROR] ASYNC run_setup_scripts: Failed to find imported statement lists: {e}")
        raise # Fail setup if statements aren't loaded

    # Define the order of execution
    all_statements_groups = {
        "RELATIONSHIP_CONSTRAINTS": relationship_constraints, # Run relationship constraints early
        # "APOC_PROCEDURES": apoc_procedures, # REMOVE or COMMENT OUT this line
        "CONCEPT_CONSTRAINTS": constraints_statements,
        "CATEGORIES": category_statements,
        "SUBCATEGORIES": [], # Add if you have separate subcategory statements
        "CONCEPTS_STRUCTURE": concept_structure, # Other concept structure if any
        # Keep samples last
        "SAMPLE_CONCEPTS": sample_concepts,
    }

    print(f"\nASYNC Running setup scripts for database: {database_name}")
    start_time = time.time()

    for group_name, statements in all_statements_groups.items():
        if not statements:
            print(f"--- ASYNC Skipping {group_name} (No statements found or file missing) ---")
            continue

        print(f"\n--- ASYNC Running {group_name} ---")
        group_start_time = time.time()
        try:
            # Use the existing execution helper
            await execute_cypher_statements(driver, statements, group_name, database_name)
            group_duration = time.time() - group_start_time
            statement_count = len(statements) # Use the count from the parsed list
            print(f"--- ASYNC Finished {group_name} ({statement_count} potential statements) in {group_duration:.2f}s ---")

        except Exception as e: # Catch errors raised by execute_cypher_statements
            # Error already printed inside execute_cypher_statements
            print(f"--- ASYNC ABORTED Setup for {database_name} due to error in {group_name} ---")
            raise # Re-raise to stop the test setup

    total_duration = time.time() - start_time
    print(f"\n--- ASYNC Completed all setup scripts for {database_name} in {total_duration:.2f}s ---")


# --- Main Execution Block (for direct script running, needs async handling) ---
async def main():
    print("Starting Neo4j Database Setup Script...")
    # Note: Direct execution of this script is complex due to async requirements
    # It's primarily intended to be used by test fixtures now.
    # For manual setup, consider adapting or using cypher-shell.

    # Example of how you might manually run it (requires async context)
    from src.db.neo4j_driver import get_driver as get_async_driver, close_driver as close_async_driver # Assuming these are async now

    driver = None
    try:
        driver = await get_async_driver() # Assuming get_driver is now async
        if driver:
            print(f"Clearing database {NEO4J_DATABASE}...")
            await clear_database(driver, NEO4J_DATABASE)
            print(f"Running setup scripts for {NEO4J_DATABASE}...")
            await run_setup_scripts(driver, NEO4J_DATABASE, include_samples=True)
            print("Manual setup script execution finished successfully.")
        else:
            print("[ERROR] Failed to get async Neo4j driver.")
    except Exception as e:
        print(f"[ERROR] Manual setup failed: {e}")
        traceback.print_exc()
    finally:
        if driver:
            await close_async_driver() # Assuming close_driver is async
            print("Async Neo4j connection closed.")

if __name__ == "__main__":
    print("Running setup script manually...")
    asyncio.run(main()) 