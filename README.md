# PRISM-Core

**Core LLM and Vector Database Services for Autonomous Manufacturing**

PRISM-Core is the foundational service layer that provides LLM (Large Language Model) capabilities and vector database management for the PRISM (PRocess Intelligence and Smart Manufacturing) ecosystem. It serves as the backbone for AI-powered manufacturing applications, offering scalable, production-ready services for natural language processing and semantic search.

## 🚀 Overview

PRISM-Core provides essential AI services that enable intelligent manufacturing applications:

- **LLM Service**: High-performance language model inference with vLLM
- **Vector Database**: Weaviate-based semantic search and document management
- **Tool Framework**: Extensible tool system for AI agents
- **API Gateway**: RESTful APIs for seamless integration

### Key Features

- **High-Performance LLM Inference**: Optimized language model serving with vLLM
- **Semantic Search**: Advanced vector search capabilities with Weaviate
- **Automatic Embedding Management**: Self-healing vector embeddings
- **Extensible Tool System**: Plugin-based tool architecture
- **Production-Ready APIs**: Scalable REST API endpoints
- **Docker Integration**: Containerized deployment for easy scaling

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PRISM-Core    │    │     Weaviate    │    │      vLLM       │
│                 │    │   Vector DB     │    │   LLM Service   │
│ ┌─────────────┐ │    │                 │    │                 │
│ │FastAPI App  │◄┼────┼►│Document Store │ │    │ ┌─────────────┐ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │Model Serving│ │
│                 │    │                 │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │                 │
│ │Vector DB API│◄┼────┼►│Search Engine│ │    │ ┌─────────────┐ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │Text Gen     │ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Model Store   │
│   (Metadata)    │    │   (Sessions)    │    │   (Weights)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ System Requirements

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **System Resources**:
  - **CPU**: 8+ cores (for LLM inference)
  - **RAM**: 16GB+ (minimum), 32GB+ (recommended)
  - **Storage**: 50GB+ SSD
  - **GPU**: NVIDIA GPU with 8GB+ VRAM (optional, for acceleration)

## 📦 Installation

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/PRISM-System/prism-core.git
   cd prism-core
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Verify installation**
   ```bash
   curl http://localhost:8000/
   # Should return: {"message": "Welcome to PRISM Core", "version": "0.1.0"}
   ```

### Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Weaviate**
   ```bash
   # Start Weaviate
   docker run -d \
     --name weaviate \
     -p 8080:8080 \
     -e QUERY_DEFAULTS_LIMIT=25 \
     -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
     -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
     -e DEFAULT_VECTORIZER_MODULE='text2vec-transformers' \
     -e ENABLE_MODULES='text2vec-transformers' \
     -e TRANSFORMERS_INFERENCE_API='http://t2v-transformers:8080' \
     semitechnologies/weaviate:1.25.8
   ```

3. **Start the application**
   ```bash
   python main.py
   ```

## 🚀 Usage

### API Endpoints

#### Vector Database API

```bash
# Create an index
curl -X POST "http://localhost:8000/api/vector-db/indices" \
  -H "Content-Type: application/json" \
  -d '{
    "class_name": "Document",
    "description": "Document storage",
    "vector_dimension": 384,
    "encoder_model": "sentence-transformers/all-MiniLM-L6-v2"
  }'

# Add documents
curl -X POST "http://localhost:8000/api/vector-db/documents/Document/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "Sample Document",
      "content": "This is a sample document for testing.",
      "metadata": {"source": "test"}
    }
  ]'

# Search documents
curl -X POST "http://localhost:8000/api/vector-db/search/Document" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sample document",
    "limit": 5
  }'
```

#### LLM Service API

```bash
# Text generation
curl -X POST "http://localhost:8001/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-0.6B",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### Python Client

```python
import requests

# Vector DB operations
def search_documents(query: str, class_name: str = "Document"):
    response = requests.post(
        f"http://localhost:8000/api/vector-db/search/{class_name}",
        json={"query": query, "limit": 5}
    )
    return response.json()

# LLM operations
def generate_text(prompt: str, model: str = "Qwen/Qwen3-0.6B"):
    response = requests.post(
        "http://localhost:8001/v1/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json()
```

## 🧪 Testing

### Run the test suite

```bash
# Comprehensive testing
python -m pytest tests/ -v

# Specific test categories
python -m pytest tests/test_vector_db.py -v
python -m pytest tests/test_llm_service.py -v
python -m pytest tests/test_api.py -v
```

### Manual testing

```bash
# Test vector database
python test_db.py

# Test client functionality
python test_client.py

# Test vector database demo
python vector_db_demo.py
```

## 📚 Documentation

- **[Server Guide](server.md)**: Server-side setup and configuration
- **[Client Guide](client.md)**: Client integration guidelines
- **[API Reference](docs/api.md)**: Detailed API documentation

## 🔧 Development

### Project Structure

```
prism-core/
├── core/
│   ├── llm/              # LLM service components
│   ├── vector_db/        # Vector database components
│   ├── tools/            # Tool framework
│   └── data/             # Data management
├── tests/                # Test files
├── docs/                 # Documentation
├── docker/               # Docker configurations
├── main.py              # FastAPI application
└── requirements.txt     # Dependencies
```

### Adding New Tools

1. Create a new tool class in `core/tools/`
2. Inherit from `BaseTool`
3. Implement required methods
4. Register in the tool registry

### Adding New Vector DB Features

1. Extend `WeaviateClient` in `core/vector_db/client.py`
2. Add corresponding API endpoints in `core/vector_db/api.py`
3. Update schemas in `core/vector_db/schemas.py`

## 🚀 Deployment

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with proper environment variables
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
docker-compose -f docker-compose.prod.yml logs -f
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n prism-core
kubectl get services -n prism-core
```

## 🔒 Security

### API Security

- **Authentication**: JWT-based authentication
- **Rate Limiting**: Configurable rate limits
- **CORS**: Cross-origin resource sharing configuration
- **Input Validation**: Comprehensive input sanitization

### Data Security

- **Encryption**: Data encryption at rest and in transit
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: Comprehensive audit trails
- **Backup**: Automated backup and recovery

## 📈 Monitoring

### Health Checks

```bash
# Service health
curl http://localhost:8000/health

# Vector DB status
curl http://localhost:8000/api/vector-db/status

# LLM service status
curl http://localhost:8001/v1/models
```

### Metrics

- **Prometheus**: Built-in metrics collection
- **Grafana**: Dashboard for visualization
- **Logging**: Structured logging with ELK stack support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/PRISM-System/prism-core/issues)
- **Documentation**: [Wiki](https://github.com/PRISM-System/prism-core/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/PRISM-System/prism-core/discussions)

## 🔗 Related Projects

- **[PRISM-Orch](https://github.com/PRISM-System/PRISM-Orch)**: AI agent orchestration system
- **[PRISM-AGI](https://github.com/PRISM-System/prism-agi)**: Main PRISM platform

---

**PRISM-Core** - The foundation for intelligent manufacturing systems.
