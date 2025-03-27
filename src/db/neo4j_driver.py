import os
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver: Driver | None = None

def get_driver() -> Driver:
    """
    Initializes and returns the Neo4j driver instance.
    Uses singleton pattern to reuse the driver.
    """
    global driver
    if driver is None:
        if not NEO4J_URI or not NEO4J_USERNAME or not NEO4J_PASSWORD:
            raise ValueError("Neo4j connection details (URI, USERNAME, PASSWORD) not found in environment variables.")
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            # Verify connection
            driver.verify_connectivity()
            print("Successfully connected to Neo4j.")
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            # Optionally re-raise or handle differently
            raise
    return driver

def close_driver():
    """Closes the Neo4j driver connection if it exists."""
    global driver
    if driver is not None:
        driver.close()
        driver = None
        print("Neo4j driver closed.")

# Example usage (optional, for testing connection directly)
# if __name__ == "__main__":
#     try:
#         test_driver = get_driver()
#         print("Driver obtained successfully.")
#         # You could run a simple query here for testing
#         # test_driver.execute_query("MATCH (n) RETURN count(n) AS count")
#     except Exception as e:
#         print(f"Error during driver test: {e}")
#     finally:
#         close_driver()
