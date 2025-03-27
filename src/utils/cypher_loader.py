import re
import os
from pathlib import Path
from functools import lru_cache

# Define the path to the query templates file relative to this file's location
# Assuming this file is src/utils/cypher_loader.py
# Go up one level (to src), then down to understanding/queries
QUERY_FILE_PATH = Path(__file__).parent.parent / "understanding/queries/query_templates.cypher"

# Regex to find the apoc.custom.asProcedure call and extract name and query
# It looks for:
# apoc.custom.asProcedure(
#   'procedure_name',  <-- Captures this (group 1)
#   'query_string',    <-- Captures this (group 2)
#   ...
# );
# It handles potential whitespace and single quotes around the arguments.
PROCEDURE_REGEX = re.compile(
    r"apoc\.custom\.asProcedure\s*\(\s*"  # Start of the call
    r"'(?P<name>[^']+)'\s*,"             # First argument: procedure name (captured)
    r"\s*'(?P<query>.*?)'\s*,"           # Second argument: query string (captured non-greedily)
    r".*?\);"                            # The rest of the arguments and closing );
    , re.DOTALL | re.IGNORECASE          # DOTALL makes . match newlines, IGNORECASE for apoc.
)

@lru_cache(maxsize=None) # Cache the results of loading the file
def _load_all_queries() -> dict[str, str]:
    """Loads all queries from the template file and caches them."""
    queries = {}
    if not QUERY_FILE_PATH.is_file():
        raise FileNotFoundError(f"Query template file not found at: {QUERY_FILE_PATH}")

    try:
        with open(QUERY_FILE_PATH, 'r') as f:
            content = f.read()

        for match in PROCEDURE_REGEX.finditer(content):
            name = match.group('name')
            query = match.group('query')
            # Basic cleaning: remove leading/trailing whitespace from the query
            queries[name] = query.strip()

        if not queries:
            print(f"Warning: No queries extracted from {QUERY_FILE_PATH}. Check file content and regex.")

    except Exception as e:
        print(f"Error reading or parsing query template file {QUERY_FILE_PATH}: {e}")
        # Depending on requirements, you might want to raise the error
        # raise

    return queries

def load_query(query_name: str) -> str:
    """
    Loads a specific Cypher query string by its procedure name
    from the query_templates.cypher file.

    Args:
        query_name: The name of the procedure associated with the query
                    (e.g., 'getConceptsByCategory').

    Returns:
        The raw Cypher query string.

    Raises:
        FileNotFoundError: If the template file cannot be found.
        KeyError: If the specified query_name is not found in the file.
    """
    all_queries = _load_all_queries()
    if query_name not in all_queries:
        raise KeyError(f"Query '{query_name}' not found in {QUERY_FILE_PATH}. Available: {list(all_queries.keys())}")
    return all_queries[query_name]

# Example usage (optional, for testing the loader directly)
# if __name__ == "__main__":
#     try:
#         print(f"Attempting to load queries from: {QUERY_FILE_PATH.resolve()}")
#         q = load_query('getConceptsByCategory')
#         print("--- getConceptsByCategory ---")
#         print(q)
#         print("\n--- Loading all ---")
#         all_q = _load_all_queries()
#         print(f"Loaded {len(all_q)} queries: {list(all_q.keys())}")
#     except (FileNotFoundError, KeyError, Exception) as e:
#         print(f"Error during loader test: {e}")
