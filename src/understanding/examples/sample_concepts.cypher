// Sample Concepts - Neo4j Implementation
// This file contains example concept creation and relationships that demonstrate the Kantian framework

// Create a substance concept "Ball" and an accident concept "Red"
CREATE (ball:Concept {
  id: apoc.create.uuid(), 
  name: "Ball", 
  description: "A spherical object used in games and sports",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  // Quality property - Reality represents positive determination
  quality: "Reality",
  // Modality property - Actual represents existence
  modality: "Actual"
})

CREATE (red:Concept {
  id: apoc.create.uuid(), 
  name: "Red", 
  description: "A color at the long wavelength end of the visible spectrum",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  // Quality property - Reality represents positive determination
  quality: "Reality"
});

// Create heat and expansion concepts for causality example
CREATE (heat:Concept {
  id: apoc.create.uuid(), 
  name: "Heat", 
  description: "Thermal energy transferred from one system to another",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
})

CREATE (expansion:Concept {
  id: apoc.create.uuid(), 
  name: "Expansion", 
  description: "Increase in volume or size of a material",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
});

// Create earth and moon concepts for community (reciprocal) example
CREATE (earth:Concept {
  id: apoc.create.uuid(), 
  name: "Earth", 
  description: "The third planet from the Sun in the Solar System",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
})

CREATE (moon:Concept {
  id: apoc.create.uuid(), 
  name: "Moon", 
  description: "A natural satellite of Earth",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
});

// Create forest and tree concepts for totality and plurality examples
CREATE (forest:Concept {
  id: apoc.create.uuid(), 
  name: "Forest", 
  description: "A large area covered chiefly with trees and undergrowth",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
})

CREATE (tree:Concept {
  id: apoc.create.uuid(), 
  name: "Tree", 
  description: "A woody perennial plant with a single main stem",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
});

// Create concepts for temporal relationships example
CREATE (lightning:Concept {
  id: apoc.create.uuid(), 
  name: "Lightning", 
  description: "Electric discharge in the atmosphere",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
})

CREATE (thunder:Concept {
  id: apoc.create.uuid(), 
  name: "Thunder", 
  description: "Sound caused by lightning",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Actual"
});

// Create a concept with Negation quality
CREATE (absence:Concept {
  id: apoc.create.uuid(), 
  name: "Absence", 
  description: "The state of being away or not present",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Negation",
  modality: "Actual"
});

// Create a concept with Limitation quality
CREATE (horizon:Concept {
  id: apoc.create.uuid(), 
  name: "Horizon", 
  description: "The line where the earth meets the sky",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Limitation",
  modality: "Actual"
});

// Create concepts with different modalities
CREATE (unicorn:Concept {
  id: apoc.create.uuid(), 
  name: "Unicorn", 
  description: "A mythical creature that resembles a horse with a single horn",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Possible"
})

CREATE (gravity:Concept {
  id: apoc.create.uuid(), 
  name: "Gravity", 
  description: "The force that attracts two bodies toward each other",
  confidence_score: 1.0,
  stability_status: "stable",
  source_information: "manual entry",
  creation_timestamp: datetime(),
  quality: "Reality",
  modality: "Necessary"
});

// Classify concepts according to Kantian categories
MATCH (ball:Concept {name: "Ball"})
MATCH (substance:Subcategory {name: "Substance-Accident"})
CREATE (ball)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(substance);

MATCH (red:Concept {name: "Red"})
MATCH (quality:Category {name: "Quality"})
CREATE (red)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(quality);

MATCH (heat:Concept {name: "Heat"})
MATCH (causality:Subcategory {name: "Causality"})
CREATE (heat)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(causality);

MATCH (expansion:Concept {name: "Expansion"})
MATCH (causality:Subcategory {name: "Causality"})
CREATE (expansion)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(causality);

MATCH (earth:Concept {name: "Earth"})
MATCH (community:Subcategory {name: "Community"})
CREATE (earth)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(community);

MATCH (moon:Concept {name: "Moon"})
MATCH (community:Subcategory {name: "Community"})
CREATE (moon)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(community);

MATCH (forest:Concept {name: "Forest"})
MATCH (totality:Subcategory {name: "Totality"})
CREATE (forest)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(totality);

MATCH (tree:Concept {name: "Tree"})
MATCH (plurality:Subcategory {name: "Plurality"})
CREATE (tree)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(plurality);

MATCH (lightning:Concept {name: "Lightning"})
MATCH (causality:Subcategory {name: "Causality"})
CREATE (lightning)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(causality);

MATCH (thunder:Concept {name: "Thunder"})
MATCH (causality:Subcategory {name: "Causality"})
CREATE (thunder)-[:INSTANCE_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual classification"
}]->(causality);

// Create relationships between concepts

// Create Substance-Accident relationship (HAS_PROPERTY)
MATCH (ball:Concept {name: "Ball"})
MATCH (red:Concept {name: "Red"})
CREATE (ball)-[:HAS_PROPERTY {
  confidence_score: 0.9,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(red);

// Create Causality relationship (CAUSES)
MATCH (heat:Concept {name: "Heat"})
MATCH (expansion:Concept {name: "Expansion"})
CREATE (heat)-[:CAUSES {
  confidence_score: 0.95,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(expansion);

// Create Community relationship (INTERACTS_WITH)
MATCH (earth:Concept {name: "Earth"})
MATCH (moon:Concept {name: "Moon"})
CREATE (earth)-[:INTERACTS_WITH {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(moon);

CREATE (moon)-[:INTERACTS_WITH {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(earth);

// Create Totality relationship (CONTAINS)
MATCH (forest:Concept {name: "Forest"})
MATCH (tree:Concept {name: "Tree"})
CREATE (forest)-[:CONTAINS {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(tree);

// Create Plurality relationship (IS_PART_OF)
MATCH (forest:Concept {name: "Forest"})
MATCH (tree:Concept {name: "Tree"})
CREATE (tree)-[:IS_PART_OF {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry"
}]->(forest);

// Create Temporal relationship (PRECEDES)
MATCH (lightning:Concept {name: "Lightning"})
MATCH (thunder:Concept {name: "Thunder"})
CREATE (lightning)-[:PRECEDES {
  confidence_score: 0.98,
  creation_timestamp: datetime(),
  source_information: "manual entry",
  temporal_distance: "seconds",
  temporal_unit: "seconds",
  temporal_order: 1
}]->(thunder);

// Create Spatial relationship (SPATIALLY_RELATES_TO)
MATCH (earth:Concept {name: "Earth"})
MATCH (moon:Concept {name: "Moon"})
CREATE (earth)-[:SPATIALLY_RELATES_TO {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry",
  relation_type: "orbits",
  distance: "384,400",
  spatial_unit: "km",
  spatial_dimension: "3D"
}]->(moon);

CREATE (moon)-[:SPATIALLY_RELATES_TO {
  confidence_score: 1.0,
  creation_timestamp: datetime(),
  source_information: "manual entry",
  relation_type: "orbits",
  distance: "384,400",
  spatial_unit: "km",
  spatial_dimension: "3D"
}]->(earth); 