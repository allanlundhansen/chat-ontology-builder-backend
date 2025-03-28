# Statement list generated from src/understanding/examples/sample_concepts.cypher

STATEMENTS = [
    # Initial Concept Creations
    'CREATE (ball:Concept { id: randomUUID(), name: "Ball", description: "A spherical object used in games and sports", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (red:Concept { id: randomUUID(), name: "Red", description: "A color at the long wavelength end of the visible spectrum", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality"})',
    'CREATE (heat:Concept { id: randomUUID(), name: "Heat", description: "Thermal energy transferred from one system to another", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (expansion:Concept { id: randomUUID(), name: "Expansion", description: "Increase in volume or size of a material", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (earth:Concept { id: randomUUID(), name: "Earth", description: "The third planet from the Sun in the Solar System", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (moon:Concept { id: randomUUID(), name: "Moon", description: "A natural satellite of Earth", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (forest:Concept { id: randomUUID(), name: "Forest", description: "A large area covered chiefly with trees and undergrowth", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (tree:Concept { id: randomUUID(), name: "Tree", description: "A woody perennial plant with a single main stem", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (lightning:Concept { id: randomUUID(), name: "Lightning", description: "Electric discharge in the atmosphere", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (thunder:Concept { id: randomUUID(), name: "Thunder", description: "Sound caused by lightning", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Existence/Non-existence"})',
    'CREATE (absence:Concept { id: randomUUID(), name: "Absence", description: "The state of being away or not present", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Negation", modality: "Existence/Non-existence"})',
    'CREATE (horizon:Concept { id: randomUUID(), name: "Horizon", description: "The line where the earth meets the sky", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Limitation", modality: "Existence/Non-existence"})',
    'CREATE (unicorn:Concept { id: randomUUID(), name: "Unicorn", description: "A mythical creature that resembles a horse with a single horn", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Possibility/Impossibility"})',
    'CREATE (gravity:Concept { id: randomUUID(), name: "Gravity", description: "The force that attracts two bodies toward each other", confidence_score: 1.0, stability_status: "stable", source_information: "manual entry", creation_timestamp: datetime(), quality: "Reality", modality: "Necessity/Contingency"})',

    # Classify concepts (INSTANCE_OF relationships)
    'MATCH (ball:Concept {name: "Ball"}), (substance:Subcategory {name: "Substance"}) CREATE (ball)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(substance)',
    # Note: The original file had Reality for Red, but HAS_PROPERTY is used later. Adjusting if needed.
    # 'MATCH (red:Concept {name: "Red"}), (reality:Subcategory {name: "Reality"}) CREATE (red)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(reality)',
    'MATCH (heat:Concept {name: "Heat"}), (causality:Subcategory {name: "Causality"}) CREATE (heat)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(causality)',
    'MATCH (expansion:Concept {name: "Expansion"}), (causality:Subcategory {name: "Causality"}) CREATE (expansion)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(causality)',
    'MATCH (earth:Concept {name: "Earth"}), (community:Subcategory {name: "Community"}) CREATE (earth)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(community)',
    'MATCH (moon:Concept {name: "Moon"}), (community:Subcategory {name: "Community"}) CREATE (moon)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(community)',
    'MATCH (forest:Concept {name: "Forest"}), (totality:Subcategory {name: "Totality"}) CREATE (forest)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(totality)',
    'MATCH (tree:Concept {name: "Tree"}), (plurality:Subcategory {name: "Plurality"}) CREATE (tree)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(plurality)',
    'MATCH (lightning:Concept {name: "Lightning"}), (causality:Subcategory {name: "Causality"}) CREATE (lightning)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(causality)',
    'MATCH (thunder:Concept {name: "Thunder"}), (causality:Subcategory {name: "Causality"}) CREATE (thunder)-[:INSTANCE_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual classification" }]->(causality)',

    # Semantic relationships between concepts
    'MATCH (ball:Concept {name: "Ball"}), (red:Concept {name: "Red"}) CREATE (ball)-[:HAS_PROPERTY { confidence_score: 0.9, creation_timestamp: datetime(), source_information: "manual entry" }]->(red)',
    'MATCH (heat:Concept {name: "Heat"}), (expansion:Concept {name: "Expansion"}) CREATE (heat)-[:CAUSES { confidence_score: 0.95, creation_timestamp: datetime(), source_information: "manual entry" }]->(expansion)',
    'MATCH (earth:Concept {name: "Earth"}), (moon:Concept {name: "Moon"}) CREATE (earth)-[:INTERACTS_WITH { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry" }]->(moon)',
    'MATCH (moon:Concept {name: "Moon"}), (earth:Concept {name: "Earth"}) CREATE (moon)-[:INTERACTS_WITH { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry" }]->(earth)',
    'MATCH (forest:Concept {name: "Forest"}), (tree:Concept {name: "Tree"}) CREATE (forest)-[:CONTAINS { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry" }]->(tree)',
    'MATCH (tree:Concept {name: "Tree"}), (forest:Concept {name: "Forest"}) CREATE (tree)-[:IS_PART_OF { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry" }]->(forest)',
    'MATCH (lightning:Concept {name: "Lightning"}), (thunder:Concept {name: "Thunder"}) CREATE (lightning)-[:PRECEDES { confidence_score: 0.98, creation_timestamp: datetime(), source_information: "manual entry", temporal_distance: "seconds", temporal_unit: "seconds", temporal_order: 1 }]->(thunder)',
    'MATCH (earth:Concept {name: "Earth"}), (moon:Concept {name: "Moon"}) CREATE (earth)-[:SPATIALLY_RELATES_TO { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry", relation_type: "orbits", distance: "384,400", spatial_unit: "km", spatial_dimension: "3D" }]->(moon)',
    'MATCH (moon:Concept {name: "Moon"}), (earth:Concept {name: "Earth"}) CREATE (moon)-[:SPATIALLY_RELATES_TO { confidence_score: 1.0, creation_timestamp: datetime(), source_information: "manual entry", relation_type: "orbits", distance: "384,400", spatial_unit: "km", spatial_dimension: "3D" }]->(earth)',

    # Add Concepts for Missing Subcategories
    '''MERGE (atom:Concept {name: "Atom"})
       ON CREATE SET
         atom.id = randomUUID(),
         atom.description = "The basic unit of a chemical element.",
         atom.confidence_score = 0.98,
         atom.stability_status = "stable",
         atom.source_information = "Sample Data Script",
         atom.creation_timestamp = datetime()''',
    '''MERGE (shadow:Concept {name: "Shadow"})
       ON CREATE SET
         shadow.id = randomUUID(),
         shadow.description = "A dark area or shape produced by a body coming between rays of light and a surface.",
         shadow.confidence_score = 0.95,
         shadow.stability_status = "ephemeral",
         shadow.source_information = "Sample Data Script",
         shadow.creation_timestamp = datetime(),
         shadow.quality = "Limitation"''',
    '''MERGE (vacuum:Concept {name: "Vacuum"})
       ON CREATE SET
         vacuum.id = randomUUID(),
         vacuum.description = "Space devoid of matter.",
         vacuum.confidence_score = 0.97,
         vacuum.stability_status = "stable",
         vacuum.source_information = "Sample Data Script",
         vacuum.creation_timestamp = datetime(),
         vacuum.quality = "Negation"''',

    # Link New Concepts to Subcategories
    '''MATCH (c:Concept {name: "Atom"}), (s:Subcategory {name: "Unity"})
       MERGE (c)-[r:INSTANCE_OF]->(s)
       ON CREATE SET
         r.confidence_score = 0.98,
         r.creation_timestamp = datetime(),
         r.source_information = "Sample Data Script"''',
    '''MATCH (c:Concept {name: "Shadow"}), (s:Subcategory {name: "Limitation"})
       MERGE (c)-[r:INSTANCE_OF]->(s)
       ON CREATE SET
         r.confidence_score = 0.95,
         r.creation_timestamp = datetime(),
         r.source_information = "Sample Data Script"''',
    '''MATCH (c:Concept {name: "Vacuum"}), (s:Subcategory {name: "Negation"})
       MERGE (c)-[r:INSTANCE_OF]->(s)
       ON CREATE SET
         r.confidence_score = 0.97,
         r.creation_timestamp = datetime(),
         r.source_information = "Sample Data Script"'''
] 