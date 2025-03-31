"""
Utility functions for data conversion.
"""
import datetime
from typing import Dict, Any, Optional, Union, List

# Note: This function needs to handle potential neo4j specific types
# without explicitly importing neo4j driver types to keep utils generic.
# It relies on duck typing (checking for 'to_native').

def convert_neo4j_datetimes(data: Optional[Any]) -> Optional[Any]:
    """
    Recursively converts Neo4j temporal types (like DateTime, Date, Time, Duration)
    within dictionaries and lists to their Python native equivalents.
    Handles nested structures.
    """
    if data is None:
        return None

    # Check for Neo4j temporal types using duck typing
    if hasattr(data, 'to_native') and callable(data.to_native):
        try:
            return data.to_native()
        except AttributeError:
            # Handle cases where to_native might exist but fail
            print(f"WARN: Could not convert value using to_native(): {data}")
            return data # Return original data if conversion fails

    # Handle dictionaries
    if isinstance(data, dict):
        native_data = {}
        for key, value in data.items():
            native_data[key] = convert_neo4j_datetimes(value) # Recurse
        return native_data

    # Handle lists
    if isinstance(data, list):
        return [convert_neo4j_datetimes(item) for item in data] # Recurse

    # Return data unchanged if it's not a dict, list, or known temporal type
    return data 