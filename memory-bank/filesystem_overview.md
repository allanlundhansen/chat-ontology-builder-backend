# Filesystem Overview

This document provides a high-level overview of the project's directory and file structure. Common Python artifacts like `__pycache__` directories and `__init__.py` files are omitted for clarity unless they are the only item in a directory.

/
├── .cursor/
│   └── rules/
│       ├── general.mdc
│       └── memory-bank.mdc
├── .git/                      # Git repository data (usually hidden)
├── .pytest_cache/             # Pytest cache (usually ignored)
├── .env                       # Environment variables (usually ignored)
├── .gitignore                 # Git ignore rules
├── docs/
│   ├── design-docs/
│   │   └── Philosophical-Considerations-Category-Implementation.md
│   ├── product-requirements/
│   │   ├── Phase 1/
│   │   │   ├── 01-Kantian-Category-Structure-KG.md
│   │   │   ├── 02-General-Logic-Module-IO-Logic.md
│   │   │   ├── 03-SHACL-Constraints-Categorical-Framework.md
│   │   │   ├── 04-Understanding-Module-API-Layer.md
│   │   │   ├── 05-Basic-Action-Sense-Layer-LLM.md
│   │   │   ├── 06-Concept-Transition-Pipeline.md
│   │   │   ├── 07-Neural-Symbolic-Bridge-Phase1.md
│   │   │   ├── 08-Chat-Integration-Service.md
│   │   │   └── Phase1Epic.md
│   │   ├── Phase 2/
│   │   │   └── Phase2Epic.md
│   │   ├── Phase 3/
│   │   │   └── Phase3Epic.md
│   │   ├── Phase 4/
│   │   │   └── Phase4Epic.md
│   │   └── Phase 5/
│   │       └── Phase5Epic.md
│   ├── current_tasks.md
│   ├── done_tasks.md
│   ├── general PRD format.md
│   └── icebox.md
├── foundation/
│   └── FullPaper.md
├── memory-bank/
│   ├── activeContext.md
│   ├── filesystem_overview.md # This file
│   ├── productContext.md
│   ├── progress.md
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   └── techContext.md
├── scripts/
│   ├── cypher_statements/
│   │   ├── category_structure_statements.py
│   │   ├── concept_structure_statements.py
│   │   └── sample_concept_statements.py
│   └── setup_database.py
├── src/
│   ├── api/
│   │   ├── middleware/
│   │   │   └── validation.py
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── categories.py
│   │           ├── concepts.py
│   │           └── relationships.py
│   ├── db/
│   │   ├── cypher_queries.py
│   │   └── neo4j_driver.py
│   ├── models/
│   │   ├── concept.py
│   │   ├── path.py
│   │   └── relationship.py
│   ├── services/
│   │   ├── concept_service.py
│   │   └── relationship_service.py
│   ├── understanding/
│   │   ├── examples/
│   │   │   └── sample_concepts.cypher
│   │   ├── queries/
│   │   │   └── query_templates.cypher
│   │   ├── schema/
│   │   │   ├── category_structure.cypher
│   │   │   ├── concept_structure.cypher
│   │   │   └── relationship_types.cypher
│   │   ├── tests/
│   │   │   └── validation_queries.cypher
│   │   └── README.md
│   ├── utils/
│   │   └── cypher_loader.py
│   ├── validation/
│   │   └── kantian_validator.py
│   └── main.py                  # Main FastAPI application entry point
├── tests/
│   ├── api/
│   │   └── v1/
│   │       ├── test_categories.py
│   │       └── test_concepts.py
│   ├── integration/
│   │   ├── test_concept_endpoints.py
│   │   ├── test_relationship_endpoints.py
│   │   └── test_validation_errors.py
│   ├── conftest.py
│   ├── test_kantian_validation.py
│   └── test_main.py
├── README.md                  # Project Readme
├── poetry.lock                # Poetry dependency lock file
└── pyproject.toml             # Project configuration (Poetry)

*Last updated: (Current Date)* 