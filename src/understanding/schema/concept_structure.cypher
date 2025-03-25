// Concept Structure - Neo4j Implementation
// This file creates the concept node structure and constraints

// Create constraints for unique concept IDs
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;

// Create indexes for efficient retrieval
CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name);
CREATE INDEX category_name_index IF NOT EXISTS FOR (c:Category) ON (c.name);
CREATE INDEX subcategory_name_index IF NOT EXISTS FOR (c:Subcategory) ON (c.name);
CREATE INDEX concept_confidence_index IF NOT EXISTS FOR (c:Concept) ON (c.confidence_score);
CREATE INDEX concept_stability_index IF NOT EXISTS FOR (c:Concept) ON (c.stability_status);
// Add indexes for Quality and Modality properties
CREATE INDEX concept_quality_index IF NOT EXISTS FOR (c:Concept) ON (c.quality);
CREATE INDEX concept_modality_index IF NOT EXISTS FOR (c:Concept) ON (c.modality);

// Define property existence constraints
CREATE CONSTRAINT concept_name_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS NOT NULL;
CREATE CONSTRAINT concept_creation_timestamp_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.creation_timestamp IS NOT NULL;

// Define property type constraints (Neo4j 4.4+)
// Note: These are optional and depend on Neo4j version
// CREATE CONSTRAINT concept_confidence_is_number IF NOT EXISTS FOR (c:Concept) REQUIRE c.confidence_score IS ::FLOAT;
// CREATE CONSTRAINT concept_stability_is_string IF NOT EXISTS FOR (c:Concept) REQUIRE c.stability_status IS ::STRING;

// Define Quality property value constraints
// This ensures quality values align with Kant's Quality categories
CREATE CONSTRAINT quality_values IF NOT EXISTS 
FOR (c:Concept) 
WHERE c.quality IS NOT NULL
REQUIRE c.quality IN ["Reality", "Negation", "Limitation"];

// Define Modality property value constraints
// This ensures modality values align with Kant's Modality categories
CREATE CONSTRAINT modality_values IF NOT EXISTS 
FOR (c:Concept) 
WHERE c.modality IS NOT NULL
REQUIRE c.modality IN ["Possible", "Actual", "Necessary"];

// Define standard properties for Concept nodes
// This is a comment to document the expected structure of Concept nodes
/*
Concept node structure:
- id: UUID - unique identifier for the concept
- name: String - name of the concept
- description: String - description of the concept
- confidence_score: Float (0.0-1.0) - confidence in the concept
- stability_status: String ("ephemeral" or "stable") - stability of the concept
- source_information: String - source of the concept
- creation_timestamp: DateTime - when the concept was created
- quality: String (optional) - Quality category: "Reality", "Negation", or "Limitation"
- modality: String (optional) - Modality category: "Possible", "Actual", or "Necessary"
- other optional properties depending on the concept type
*/ 