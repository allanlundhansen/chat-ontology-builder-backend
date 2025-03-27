import os
import argparse
from neo4j import GraphDatabase, Driver, exceptions as neo4j_exceptions
from dotenv import load_dotenv

# --- Configuration ---

# Define the order of scripts to execute
# Paths are relative to the project root directory
CYPHER_SCRIPTS = [
    "src/understanding/schema/category_structure.cypher",
    "src/understanding/schema/concept_structure.cypher",
    "src/understanding/schema/relationship_types.cypher", # Recommended, contains constraints
    "src/understanding/examples/sample_concepts.cypher",  # Contains actual data
]

# Load environment variables from a .env file if it exists
load_dotenv()

# Neo4j Connection Details (fetched from environment variables)
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# IMPORTANT: Use environment variables for passwords in production!
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password") # Replace "password" with your default if needed

# --- Helper Functions ---

def execute_cypher_script(driver: Driver, script_path: str):
    """Reads and executes an entire Cypher script file."""
    print(f"Attempting to execute script: {script_path}...")
    try:
        # Ensure path is relative to the project root where this script is expected to run
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', script_path))
        if not os.path.exists(full_path):
            print(f"  [ERROR] Script file not found: {full_path}")
            return False

        with open(full_path, 'r', encoding='utf-8') as f:
            cypher_query = f.read()

        if not cypher_query.strip():
            print("  [WARN] Script file is empty.")
            return True # Treat empty script as success

        # Execute the entire script content.
        # For very large data files, consider splitting, but these should be okay.
        driver.execute_query(cypher_query, database_="neo4j")
        print(f"  [SUCCESS] Executed script: {script_path}")
        return True

    except neo4j_exceptions.Neo4jError as db_error:
        print(f"  [ERROR] Database error executing script {script_path}: {db_error}")
        return False
    except IOError as io_error:
        print(f"  [ERROR] File reading error for script {script_path}: {io_error}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error executing script {script_path}: {e}")
        return False

def clear_database(driver: Driver):
    """Clears all nodes and relationships from the database."""
    print("Attempting to clear the database...")
    try:
        # Check constraints first - DETACH DELETE might fail if constraints exist on empty DB
        # It's generally safe to just run DETACH DELETE
        driver.execute_query("MATCH (n) DETACH DELETE n;", database_="neo4j")
        print("  [SUCCESS] Database cleared.")
        return True
    except neo4j_exceptions.Neo4jError as db_error:
        print(f"  [ERROR] Database error clearing database: {db_error}")
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error clearing database: {e}")
        return False

# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup Neo4j database schema and sample data.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the entire database before running setup scripts."
    )
    args = parser.parse_args()

    driver = None
    try:
        # Establish connection
        print(f"Connecting to Neo4j at {NEO4J_URI}...")
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("  [SUCCESS] Connected to Neo4j.")

        # Clear database if requested
        if args.clear:
            if not clear_database(driver):
                print("Halting script due to error during database clearing.")
                exit(1) # Exit with error code

        # Execute setup scripts in order
        print("\nStarting script execution...")
        for script_file in CYPHER_SCRIPTS:
            if not execute_cypher_script(driver, script_file):
                print(f"\nHalting script due to error in: {script_file}")
                exit(1) # Exit with error code

        print("\nDatabase setup completed successfully!")

    except neo4j_exceptions.AuthError:
        print(f"[FATAL ERROR] Neo4j authentication failed for user '{NEO4J_USER}'. Check credentials.")
        exit(1)
    except neo4j_exceptions.ServiceUnavailable:
        print(f"[FATAL ERROR] Could not connect to Neo4j at {NEO4J_URI}. Ensure the database is running.")
        exit(1)
    except Exception as e:
        print(f"[FATAL ERROR] An unexpected error occurred: {e}")
        exit(1)
    finally:
        # Ensure the driver is closed
        if driver:
            driver.close()
            print("\nNeo4j connection closed.") 