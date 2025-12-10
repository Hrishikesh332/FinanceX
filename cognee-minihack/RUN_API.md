# Running the Agentic API

## Quick Start

### 1. Start the API Server

```bash
cd /Users/hrishikesh/Desktop/Finance/cognee-minihack
source .venv/bin/activate
python agentic.py
```

The API will be available at: `http://localhost:8000`

### 2. Test the API

#### Using curl:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What vendors do we have?"}'
```

#### Using Python:
```bash
python demo_api.py
```

#### Using the interactive API documentation:
Open your browser and go to: `http://localhost:8000/docs`

## API Endpoint

### POST /query

**Request:**
```json
{
  "question": "Your natural language question here"
}
```

**Response:**
```json
{
  "answer": "The answer from the knowledge graph",
  "question": "Your original question"
}
```

## Example Questions

- "What vendors do we have?"
- "Can you list all transactions from Vendor 2?"
- "What is the total amount we paid to all vendors?"
- "Did we buy any laptops from Vendor 3?"
- "Which vendors give us the most discounts?"

## Troubleshooting

### Ollama not responding
Make sure Ollama is running:
```bash
brew services status ollama
# If not running:
brew services start ollama
```

### Models not found
Register the models:
```bash
cd /Users/hrishikesh/Desktop/Finance/models
ollama create nomic-embed-text -f nomic-embed-text/Modelfile
ollama create cognee-distillabs-model-gguf-quantized -f cognee-distillabs-model-gguf-quantized/Modelfile
```

### Check model status
```bash
ollama list
```

Should show:
- `cognee-distillabs-model-gguf-quantized:latest`
- `nomic-embed-text:latest`

