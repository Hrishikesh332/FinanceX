# Running FinanceX Services

## Quick Start - Single Command

Run all services together using the main entry point:

```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python app.py
```

This starts all services on **port 8000** with the following paths:
- **Main API**: `http://localhost:8000/api/*`
- **Data API**: `http://localhost:8000/data/*`
- **KPI API**: `http://localhost:8000/kpi/*`

## Service Architecture

```
app.py (Port 8000)
├── /api/*  → services/api.py (Chat & Ingestion)
├── /data/* → services/data.py (CSV Data)
└── /kpi/*  → services/kpi.py (Knowledge Graph KPIs)
```

## Available Endpoints

### Root
- `GET /` - Service information
- `GET /health` - Health check for all services
- `GET /docs` - Swagger UI (all services)
- `GET /redoc` - ReDoc documentation

### Data API (`/data/*`)
- `GET /data/invoices` - Get all invoices from CSV
- `GET /data/transactions` - Get all transactions from CSV

### KPI API (`/kpi/*`)
- `GET /kpi/kpis` - Get KPIs from knowledge graph
- `GET /kpi/health` - KPI service health check

### Main API (`/api/*`)
- `POST /api/v1/chat` - Chat with knowledge graph
- `POST /api/v1/ingest/invoices` - Ingest invoice data
- `POST /api/v1/ingest/transactions` - Ingest transaction data
- `GET /api/v1/stats` - Get graph statistics

## Running Services Individually

If you prefer to run services on separate ports:

### Terminal 1: Data API (Port 8001)
```bash
cd cognee-minihack
source .venv/bin/activate
python services/data.py
```

### Terminal 2: KPI API (Port 8002)
```bash
cd cognee-minihack
source .venv/bin/activate
python services/kpi.py
```

### Terminal 3: Main API (Port 8003)
```bash
cd cognee-minihack
source .venv/bin/activate
python services/api.py
```

## Prerequisites

### 1. Install Dependencies
```bash
cd cognee-minihack
source .venv/bin/activate
uv pip install -r requirements_api.txt
```

### 2. Setup Ollama
```bash
# Install Ollama
brew install ollama

# Start Ollama service
brew services start ollama

# Register models
cd ../models
ollama create nomic-embed-text -f nomic-embed-text/Modelfile
ollama create cognee-distillabs-model-gguf-quantized -f cognee-distillabs-model-gguf-quantized/Modelfile
```

### 3. Load Knowledge Graph
```bash
cd cognee-minihack
source .venv/bin/activate
python setup.py
```

## Testing the Services

### Test Main App
```bash
# Get service info
curl http://localhost:8000/

# Health check
curl http://localhost:8000/health

# Get invoices
curl http://localhost:8000/data/invoices | jq '.[0]'

# Get KPIs
curl http://localhost:8000/kpi/kpis | jq '.'

# Chat query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How many invoices do we have?"}'
```

## Frontend Integration

Update Frontend to use the unified API on port 8000:

### Before (Multiple Ports):
```typescript
fetch('http://localhost:8001/invoices')  // Data API
fetch('http://localhost:8002/kpis')      // KPI API
```

### After (Single Port):
```typescript
fetch('http://localhost:8000/data/invoices')  // Data API
fetch('http://localhost:8000/kpi/kpis')       // KPI API
fetch('http://localhost:8000/api/v1/chat')    // Main API
```

## File Structure

```
cognee-minihack/
├── app.py                    # Main entry point (runs all services)
├── services/
│   ├── api.py               # Main API (chat, ingestion)
│   ├── data.py              # Data API (CSV access)
│   ├── kpi.py               # KPI API (knowledge graph metrics)
│   ├── README.md            # Services documentation
│   └── test_data_api.py     # Data API tests
├── agentic.py               # Simple query-only API (alternative)
├── requirements_api.txt     # API dependencies
└── RUN_SERVICES.md          # This file
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Ollama Not Running
```bash
# Check if Ollama is running
ollama list

# Start Ollama
brew services start ollama
```

### Knowledge Graph Not Loaded
```bash
# Re-run setup
cd cognee-minihack
source .venv/bin/activate
python setup.py
```

### Import Errors
```bash
# Reinstall dependencies
cd cognee-minihack
source .venv/bin/activate
uv pip install -r requirements_api.txt
```

## Production Deployment

For production, use a process manager like systemd or supervisor:

```bash
# Using uvicorn with workers
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with gunicorn:

```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Environment Variables

Set these before running:

```bash
export LLM_API_KEY="."
export LLM_PROVIDER="ollama"
export LLM_MODEL="cognee-distillabs-model-gguf-quantized"
export LLM_ENDPOINT="http://localhost:11434/v1"
export EMBEDDING_MODEL="nomic-embed-text:latest"
```

---

**Recommended**: Use `python app.py` for the simplest setup with all services on one port!

