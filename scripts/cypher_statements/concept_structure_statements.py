# Statement list generated from src/understanding/schema/concept_structure.cypher

STATEMENTS = [
    # --- Constraints for Concepts ---
    # Ensure Concept has a UUID id and it's unique. Implicitly creates an index.
    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT concept_id_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS NOT NULL", # Ensure ID always exists

    # Ensure Concept name exists (useful for lookups)
    "CREATE CONSTRAINT concept_name_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS NOT NULL",
    # Optionally, if names should be unique (consider if this is always true)
    # "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",

    # --- Indexes for Concepts ---
    # Index on name for faster lookups by name
    "CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name)",

    # Index on properties used for classification and filtering
    "CREATE INDEX concept_quality_index IF NOT EXISTS FOR (c:Concept) ON (c.quality)",
    "CREATE INDEX concept_modality_index IF NOT EXISTS FOR (c:Concept) ON (c.modality)",
    "CREATE INDEX concept_confidence_score_index IF NOT EXISTS FOR (c:Concept) ON (c.confidence_score)",
    "CREATE INDEX concept_stability_status_index IF NOT EXISTS FOR (c:Concept) ON (c.stability_status)",
    "CREATE INDEX concept_creation_timestamp_index IF NOT EXISTS FOR (c:Concept) ON (c.creation_timestamp)",

    # --- Constraints/Indexes for Relationships (Optional but recommended) ---
    # Example: Ensure relationship properties exist if needed
    # "CREATE CONSTRAINT rel_confidence_exists IF NOT EXISTS FOR ()-[r]-() REQUIRE r.confidence_score IS NOT NULL",
    # "CREATE CONSTRAINT rel_timestamp_exists IF NOT EXISTS FOR ()-[r]-() REQUIRE r.creation_timestamp IS NOT NULL",

    # Example: Index on relationship properties if frequently queried
    # "CREATE INDEX rel_confidence_index IF NOT EXISTS FOR ()-[r]-() ON (r.confidence_score)"
] 