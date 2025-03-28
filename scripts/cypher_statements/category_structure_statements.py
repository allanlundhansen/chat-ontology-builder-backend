# Statement list generated from src/understanding/schema/category_structure.cypher

STATEMENTS = [
    # Constraints
    "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT category_name_exists IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS NOT NULL",
    "CREATE CONSTRAINT subcategory_name_unique IF NOT EXISTS FOR (s:Subcategory) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT subcategory_name_exists IF NOT EXISTS FOR (s:Subcategory) REQUIRE s.name IS NOT NULL",

    # Categories
    'MERGE (quantity:Category {name: "Quantity"}) ON CREATE SET quantity.description = "Deals with the extension of concepts"',
    'MERGE (quality:Category {name: "Quality"}) ON CREATE SET quality.description = "Deals with the content of concepts"',
    'MERGE (relation:Category {name: "Relation"}) ON CREATE SET relation.description = "Deals with how concepts relate to each other"',
    'MERGE (modality:Category {name: "Modality"}) ON CREATE SET modality.description = "Deals with the relation of concepts to the faculty of cognition"',

    # Quantity Subcategories
    'MERGE (unity:Subcategory {name: "Unity"}) ON CREATE SET unity.description = "Concept of One"',
    'MERGE (plurality:Subcategory {name: "Plurality"}) ON CREATE SET plurality.description = "Concept of Many"',
    'MERGE (totality:Subcategory {name: "Totality"}) ON CREATE SET totality.description = "Concept of All"',

    # Quality Subcategories
    'MERGE (reality:Subcategory {name: "Reality"}) ON CREATE SET reality.description = "Positive determination"',
    'MERGE (negation:Subcategory {name: "Negation"}) ON CREATE SET negation.description = "Negative determination"',
    'MERGE (limitation:Subcategory {name: "Limitation"}) ON CREATE SET limitation.description = "Bounded determination"',

    # Relation Subcategories
    'MERGE (substance:Subcategory {name: "Substance"}) ON CREATE SET substance.description = "Relation of inherence and subsistence"',
    'MERGE (causality:Subcategory {name: "Causality"}) ON CREATE SET causality.description = "Relation of cause and effect"',
    'MERGE (community:Subcategory {name: "Community"}) ON CREATE SET community.description = "Reciprocal relation between agent and patient"',

    # Modality Subcategories
    'MERGE (possibility:Subcategory {name: "Possibility/Impossibility"}) ON CREATE SET possibility.description = "Agreement or conflict with conditions of experience"',
    'MERGE (existence:Subcategory {name: "Existence/Non-existence"}) ON CREATE SET existence.description = "Agreement or conflict with material conditions of experience"',
    'MERGE (necessity:Subcategory {name: "Necessity/Contingency"}) ON CREATE SET necessity.description = "Agreement or determination by material conditions of experience"',

    # Quantity Relationships
    'MATCH (cat:Category {name: "Quantity"}), (sub:Subcategory {name: "Unity"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Quantity"}), (sub:Subcategory {name: "Plurality"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Quantity"}), (sub:Subcategory {name: "Totality"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',

    # Quality Relationships
    'MATCH (cat:Category {name: "Quality"}), (sub:Subcategory {name: "Reality"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Quality"}), (sub:Subcategory {name: "Negation"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Quality"}), (sub:Subcategory {name: "Limitation"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',

    # Relation Relationships
    'MATCH (cat:Category {name: "Relation"}), (sub:Subcategory {name: "Substance"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Relation"}), (sub:Subcategory {name: "Causality"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Relation"}), (sub:Subcategory {name: "Community"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',

    # Modality Relationships
    'MATCH (cat:Category {name: "Modality"}), (sub:Subcategory {name: "Possibility/Impossibility"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Modality"}), (sub:Subcategory {name: "Existence/Non-existence"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',
    'MATCH (cat:Category {name: "Modality"}), (sub:Subcategory {name: "Necessity/Contingency"}) MERGE (cat)-[:HAS_SUBCATEGORY]->(sub)',

    # Add/Update formal definitions and examples for Quantity
    '''MATCH (unity:Subcategory {name: "Unity"})
       SET unity.formal_definition = "A concept considered as including only a single instance",
           unity.examples = ["Individual", "Unit", "Single"]''',
    '''MATCH (plurality:Subcategory {name: "Plurality"})
       SET plurality.formal_definition = "A concept considered as a collection of separate instances",
           plurality.examples = ["Many", "Collection", "Group"]''',
    '''MATCH (totality:Subcategory {name: "Totality"})
       SET totality.formal_definition = "Unity and plurality considered together as a whole",
           totality.examples = ["All", "Complete", "Whole"]''',

    # Set formal definitions and examples for Quality subcategories
    '''MATCH (reality:Subcategory {name: "Reality"})
       SET reality.formal_definition = "The affirmation of a quality",
           reality.examples = ["Being", "Presence", "Affirmation"]''',
    '''MATCH (negation:Subcategory {name: "Negation"})
       SET negation.formal_definition = "The denial of a quality",
           negation.examples = ["Not-being", "Absence", "Denial"]''',
    '''MATCH (limitation:Subcategory {name: "Limitation"})
       SET limitation.formal_definition = "The boundary between reality and negation",
           limitation.examples = ["Boundary", "Finitude", "Restriction"]''',

    # Set formal definitions and examples for Relation subcategories
    '''MATCH (substance:Subcategory {name: "Substance"})
       SET substance.formal_definition = "The relation of properties to a thing",
           substance.examples = ["Object-property", "Subject-predicate", "Inherence"]''',
    '''MATCH (causality:Subcategory {name: "Causality"})
       SET causality.formal_definition = "The relation of cause to effect",
           causality.examples = ["Cause-effect", "If-then", "Production"]''',
    '''MATCH (community:Subcategory {name: "Community"})
       SET community.formal_definition = "Reciprocal causation between active and passive",
           community.examples = ["Interaction", "Reciprocity", "Mutual influence"]''',

    # Set formal definitions and examples for Modality subcategories
    '''MATCH (possibility:Subcategory {name: "Possibility/Impossibility"})
       SET possibility.formal_definition = "Conformity or non-conformity to the formal conditions of experience",
           possibility.examples = ["Can be", "Cannot be", "Possible"]''',
    '''MATCH (existence:Subcategory {name: "Existence/Non-existence"})
       SET existence.formal_definition = "Connection or non-connection with the material conditions of experience",
           existence.examples = ["Is", "Is not", "Exists"]''',
    '''MATCH (necessity:Subcategory {name: "Necessity/Contingency"})
       SET necessity.formal_definition = "Determination or non-determination by the general conditions of experience",
           necessity.examples = ["Must be", "May be", "Required"]'''
] 