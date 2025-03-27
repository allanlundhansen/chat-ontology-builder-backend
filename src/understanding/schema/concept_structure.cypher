// Concept Structure - Neo4j Implementation
// This file creates the concept node structure and constraints

// Create constraints for unique concept IDs
CREATE CONSTRAINT concept_id_unique IF NOT EXISTS
FOR (c:Concept) 
REQUIRE c.id IS UNIQUE;

// Create indexes for efficient retrieval
CREATE INDEX concept_name_index IF NOT EXISTS
FOR (c:Concept) 
ON (c.name);

CREATE INDEX concept_confidence_index IF NOT EXISTS FOR (c:Concept) ON (c.confidence_score);
CREATE INDEX concept_stability_index IF NOT EXISTS FOR (c:Concept) ON (c.stability_status);
// Add indexes for Quality and Modality properties
CREATE INDEX concept_quality_index IF NOT EXISTS
FOR (c:Concept) 
ON (c.quality);

CREATE INDEX concept_modality_index IF NOT EXISTS
FOR (c:Concept) 
ON (c.modality);

// Define property existence constraints
CREATE CONSTRAINT concept_name_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS NOT NULL;
CREATE CONSTRAINT concept_creation_timestamp_exists IF NOT EXISTS FOR (c:Concept) REQUIRE c.creation_timestamp IS NOT NULL;

// Define property type constraints (Neo4j 4.4+)
// Note: These are optional and depend on Neo4j version
// CREATE CONSTRAINT concept_confidence_is_number IF NOT EXISTS FOR (c:Concept) REQUIRE c.confidence_score IS ::FLOAT;
// CREATE CONSTRAINT concept_stability_is_string IF NOT EXISTS FOR (c:Concept) REQUIRE c.stability_status IS ::STRING;

// Value constraints for 'quality' and 'modality' will be enforced at the application level
// due to limitations in applying enum-style constraints or using APOC triggers
// in the current Neo4j AuraDB environment.

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
- modality: String (optional) - Modality category: "Possibility/Impossibility", "Existence/Non-existence", or "Necessity/Contingency"
- other optional properties depending on the concept type
*/

// Note on Hybrid Approach:
// Quality and Modality are implemented as direct properties on Concept nodes for efficiency in querying 
// and constraint validation, while Quantity and Relation categories are represented through INSTANCE_OF 
// relationships to Subcategory nodes. This hybrid approach balances performance with expressive power. 

// --- REMOVED APOC TRIGGER INSTALLATION CALLS ---
// Trigger installation calls removed as apoc.trigger.install is unavailable/disabled in the target AuraDB environment.
// Validation for 'quality' and 'modality' values will be handled at the application level. 