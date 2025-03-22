# KantAI Backend

A Kantian-inspired neuro-symbolic AI backend framework implementing dynamic concept formation, adaptive reasoning, and structured knowledge representation.

## Overview

This backend serves as the core implementation of the Kantian-inspired cognitive architecture described in our research. It handles the integration between neural networks and symbolic reasoning, manages the knowledge graph, coordinates with LLMs, and provides a comprehensive API for frontend clients.

## Key Features

- **Neural-Symbolic Integration**: Bidirectional translation between neural embeddings and symbolic representations
- **Dynamic Ontology Management**: Self-updating knowledge graph based on Kant's categorical structure
- **LLM-Powered Data Ingestion**: Processes unstructured external data into structured concepts
- **Ethical Reasoning**: Built-in deontological constraints throughout the decision-making process (later stage)
- **Active Inference**: Resource-aware computation balancing information gain against computational cost
- **Multi-stage Verification**: Robust hallucination detection and mitigation for LLM outputs

## System Architecture

The backend implements five core cognitive modules:

1. **Understanding Module**: Neo4j GraphDB with SHACL constraints organizing knowledge according to Kant's categorical framework
2. **Imagination Module**: Generative components bridging sensory data and concepts via productive and reproductive pathways
3. **Judgment Module**: Classification and concept formation through determinant and reflective judgment processes
4. **Reason Module**: Meta-reasoning layer ensuring global coherence through active inference
5. **Action/Sense Layer**: LLM-based ingestion converting external unstructured data into symbolic representations

## Technology Stack

- **Database**: Neo4j Graph Database with SHACL constraints
- **ML Framework**: PyTorch for neural components
- **Neural-Symbolic Bridge**: Logic Tensor Networks (LTNs), Graph Neural Networks (GNNs)
- **LLM Integration**: REST API connections to external or self-hosted LLMs
- **API Layer**: FastAPI for RESTful services
- **Containerization**: Docker, Kubernetes
- **Monitoring**: Prometheus, Grafana
- **CI/CD**: GitHub Actions

## Installation

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

## Quick Start

```python
from kantai import KantAIBackend

# Initialize the backend
backend = KantAIBackend(config_path="config.yaml")

# Process unstructured data
response = backend.action_sense.process_text("The ball caused the window to break")

# Query the knowledge graph
causal_relationships = backend.understanding.query("MATCH (a)-[:CAUSES]->(b) RETURN a, b")

# Generate explanations for novel phenomena
explanation = backend.judgment.reflect(novel_data, domain="physics")
```

## API Reference

The backend exposes a comprehensive RESTful API:

### Understanding Module API
- `GET /ontology`: Returns the current ontological structure
- `GET /ontology/category/{category_id}`: Retrieves specific categorical structures
- `POST /concepts`: Registers new concept nodes
- `PUT /relationships`: Establishes or updates relationships

### Judgment Module API
- `POST /determine`: Processes inputs via determinant judgment
- `POST /reflect`: Processes novel inputs requiring reflective judgment
- `GET /stability/{concept_id}`: Returns concept stability metrics

### Action/Sense Layer API
- `POST /process`: Accepts raw sensory data and returns processed embeddings
- `POST /embed`: Transforms structured data into vector embeddings

See [API Documentation](docs/api.md) for complete details.

## Development

### Prerequisites
- Python
- Docker and Docker Compose
- Neo4j Graph Database
- GPU for neural components (recommended, but not decided)

### Running Tests
```bash
pytest tests/
```

### Building Documentation
```bash
cd docs
mkdocs build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This is a private project.

## Citation

If you use this software in your research, please cite:
```
@article{kantai2023,
  title={A Kantian-Inspired Neuro-Symbolic AI Framework for Dynamic Concept Formation and Adaptive Reasoning},
  author={Your Team},
  journal={ArXiv},
  year={2023}
}
```
