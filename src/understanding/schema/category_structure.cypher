// Kantian Category Structure - Neo4j Implementation
// This file creates the core categorical structure based on Kant's epistemology

// Create main category nodes
CREATE (quantity:Category {name: "Quantity", description: "Deals with the extension of concepts"})
CREATE (quality:Category {name: "Quality", description: "Deals with the content of concepts"})
CREATE (relation:Category {name: "Relation", description: "Deals with how concepts relate to each other"})
CREATE (modality:Category {name: "Modality", description: "Deals with the relation of concepts to the faculty of cognition"});

// Create Quantity subcategories and connect them
CREATE (unity:Subcategory {name: "Unity", description: "Concept of One"})
CREATE (plurality:Subcategory {name: "Plurality", description: "Concept of Many"})
CREATE (totality:Subcategory {name: "Totality", description: "Concept of All"})
CREATE (quantity)-[:HAS_SUBCATEGORY]->(unity)
CREATE (quantity)-[:HAS_SUBCATEGORY]->(plurality)
CREATE (quantity)-[:HAS_SUBCATEGORY]->(totality);

// Create Quality subcategories and connect them
CREATE (reality:Subcategory {name: "Reality", description: "Positive determination"})
CREATE (negation:Subcategory {name: "Negation", description: "Negative determination"})
CREATE (limitation:Subcategory {name: "Limitation", description: "Bounded determination"})
CREATE (quality)-[:HAS_SUBCATEGORY]->(reality)
CREATE (quality)-[:HAS_SUBCATEGORY]->(negation)
CREATE (quality)-[:HAS_SUBCATEGORY]->(limitation);

// Create Relation subcategories and connect them
CREATE (substance:Subcategory {name: "Substance-Accident", description: "Relation of inherence and subsistence"})
CREATE (causality:Subcategory {name: "Causality", description: "Relation of cause and effect"})
CREATE (community:Subcategory {name: "Community", description: "Reciprocal relation between agent and patient"})
CREATE (relation)-[:HAS_SUBCATEGORY]->(substance)
CREATE (relation)-[:HAS_SUBCATEGORY]->(causality)
CREATE (relation)-[:HAS_SUBCATEGORY]->(community);

// Create Modality subcategories and connect them
CREATE (possibility:Subcategory {name: "Possibility/Impossibility", description: "Agreement or conflict with conditions of experience"})
CREATE (existence:Subcategory {name: "Existence/Non-existence", description: "Agreement or conflict with material conditions of experience"})
CREATE (necessity:Subcategory {name: "Necessity/Contingency", description: "Agreement or determination by material conditions of experience"})
CREATE (modality)-[:HAS_SUBCATEGORY]->(possibility)
CREATE (modality)-[:HAS_SUBCATEGORY]->(existence)
CREATE (modality)-[:HAS_SUBCATEGORY]->(necessity);

// Add formal definitions and examples
MATCH (unity:Subcategory {name: "Unity"})
SET unity.formal_definition = "A concept considered as including only a single instance",
    unity.examples = ["Individual", "Unit", "Single"];

MATCH (plurality:Subcategory {name: "Plurality"})
SET plurality.formal_definition = "A concept considered as a collection of separate instances",
    plurality.examples = ["Many", "Collection", "Group"];

MATCH (totality:Subcategory {name: "Totality"})
SET totality.formal_definition = "Unity and plurality considered together as a whole",
    totality.examples = ["All", "Complete", "Whole"];

// Set formal definitions and examples for Quality subcategories
MATCH (reality:Subcategory {name: "Reality"})
SET reality.formal_definition = "The affirmation of a quality",
    reality.examples = ["Being", "Presence", "Affirmation"];

MATCH (negation:Subcategory {name: "Negation"})
SET negation.formal_definition = "The denial of a quality",
    negation.examples = ["Not-being", "Absence", "Denial"];

MATCH (limitation:Subcategory {name: "Limitation"})
SET limitation.formal_definition = "The boundary between reality and negation",
    limitation.examples = ["Boundary", "Finitude", "Restriction"];

// Set formal definitions and examples for Relation subcategories
MATCH (substance:Subcategory {name: "Substance-Accident"})
SET substance.formal_definition = "The relation of properties to a thing",
    substance.examples = ["Object-property", "Subject-predicate", "Inherence"];

MATCH (causality:Subcategory {name: "Causality"})
SET causality.formal_definition = "The relation of cause to effect",
    causality.examples = ["Cause-effect", "If-then", "Production"];

MATCH (community:Subcategory {name: "Community"})
SET community.formal_definition = "Reciprocal causation between active and passive",
    community.examples = ["Interaction", "Reciprocity", "Mutual influence"];

// Set formal definitions and examples for Modality subcategories
MATCH (possibility:Subcategory {name: "Possibility/Impossibility"})
SET possibility.formal_definition = "Conformity or non-conformity to the formal conditions of experience",
    possibility.examples = ["Can be", "Cannot be", "Possible"];

MATCH (existence:Subcategory {name: "Existence/Non-existence"})
SET existence.formal_definition = "Connection or non-connection with the material conditions of experience",
    existence.examples = ["Is", "Is not", "Exists"];

MATCH (necessity:Subcategory {name: "Necessity/Contingency"})
SET necessity.formal_definition = "Determination or non-determination by the general conditions of experience",
    necessity.examples = ["Must be", "May be", "Required"]; 