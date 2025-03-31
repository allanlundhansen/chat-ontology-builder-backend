# Technical Context

## Technology Stack

### Core Technologies
- **Python**: Primary programming language
- **FastAPI**: RESTful API framework
- **Neo4j**: Graph database for knowledge representation
- **PyTorch**: Machine learning framework for neural components
- **Docker/Kubernetes**: Containerization and orchestration

### Neural-Symbolic Components
- **Logic Tensor Networks (LTNs)**: For bridging neural and symbolic representations
- **Graph Neural Networks (GNNs)**: For structural learning on the knowledge graph
- **SHACL**: For graph constraints and validation

### LLM Integration
- **OpenAI API**: For external LLM access
- **HuggingFace Transformers**: For local model deployment
- **LangChain**: For LLM orchestration and augmentation

### Communication and Real-time Updates
- **WebSockets**: For real-time chat and graph updates
- **Redis**: For pub/sub messaging and caching
- **Celery**: For asynchronous task processing

### Monitoring and Logging
- **Prometheus**: For metrics collection
- **Grafana**: For visualization and dashboards
- **ELK Stack**: For centralized logging

## Development Setup

### Local Environment
```bash
# Clone the repository
git clone https://github.com/your-org/kantai-backend.git
cd kantai-backend

# Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# Start services
docker-compose up -d
```

### Required Dependencies
- Python 3.9+
- Docker and Docker Compose
- Neo4j 4.4+
- CUDA-compatible GPU (recommended for neural components)

### Development Tools
- **Poetry**: Dependency management
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Static type checking
- **pytest**: Testing framework

## Technical Constraints

### Performance Requirements
- Response time < 200ms for API endpoints
- Throughput > 100 requests/second
- Support for concurrent users > 1000

### Scalability Considerations
- Horizontal scaling for stateless components
- Vertical scaling for Neo4j database
- Caching strategy for frequently accessed data

### Security Requirements
- Authentication via JWT
- Role-based access control
- Data encryption at rest and in transit
- Regular security audits and penetration testing

### Integration Requirements
- RESTful API for frontend integration
- WebSocket endpoints for real-time updates
- Batch operations for efficient bulk modifications

### Platform Limitations Encountered
- **Neo4j AuraDB Constraints/Triggers/Procedures**: The current AuraDB environment (Neo4j 5.x) lacks support for direct "enum-style" value constraints, conditional property existence constraints (e.g., require `spatial_unit` only if `distance` exists), and does not have APOC triggers (`apoc.trigger.install`) or the procedure creation procedure (`apoc.custom.asProcedure`) enabled/available. This necessitates application-level validation for specific property values (e.g., `Concept.quality`, `Concept.modality`), conditional relationship property rules, and requires query templates to be executed by the application rather than stored as database procedures.
- Added workaround for Neo4j constraints using KantianValidator service
- Implemented application-level enforcement of conditional `spatial_unit` requirement
- **Query Management Strategy**: All Cypher queries are now managed as Python string constants within modules in the `src/cypher_queries/` directory. The file-based loader (`cypher_loader.py`) has been removed due to previous reliability concerns (caching, parsing fragility).

## Dependencies

### External Services
- Neo4j Graph Database
- LLM Provider API (OpenAI, Anthropic, etc.)
- Vector Database for embeddings (optional: Pinecone, Weaviate)

### Internal Dependencies
- Chat Ontology Builder frontend
- Authentication service
- Logging and monitoring infrastructure

## Deployment Architecture

### Development Environment
- Local Docker Compose setup
- Mock services for external dependencies
- Hot-reloading for rapid development

### Testing Environment
- Kubernetes cluster with CI/CD pipeline
- Automated testing on pull requests
- Performance and load testing

### Production Environment
- Kubernetes cluster with auto-scaling
- High availability configuration
- Scheduled backups and disaster recovery
- Monitoring and alerting 