import os
import pathlib
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import resource

# Note: Environment variables must be set BEFORE importing cognee
os.environ["LLM_API_KEY"] = "."
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["LLM_MODEL"] = "cognee-distillabs-model-gguf-quantized"
os.environ["LLM_ENDPOINT"] = "http://localhost:11434/v1"
os.environ["LLM_MAX_TOKENS"] = "16384"

os.environ["EMBEDDING_PROVIDER"] = "ollama"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text:latest"
os.environ["EMBEDDING_ENDPOINT"] = "http://localhost:11434/api/embed"
os.environ["EMBEDDING_DIMENSIONS"] = "768"
os.environ["HUGGINGFACE_TOKENIZER"] = "nomic-ai/nomic-embed-text-v1.5"

from custom_retriever import GraphCompletionRetrieverWithUserPrompt

# Increase file descriptor limit
try:
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (min(10000, hard), hard))
except Exception:
    pass

# Initialize FastAPI app
app = FastAPI(
    title="Cognee Agentic API",
    description="FastAPI service for question answering using Cognee knowledge graph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize retriever
system_prompt_path = pathlib.Path(
    os.path.join(pathlib.Path(__file__).parent, "prompts/system_prompt.txt")
).resolve()

retriever: Optional[GraphCompletionRetrieverWithUserPrompt] = None


def get_retriever() -> GraphCompletionRetrieverWithUserPrompt:
    """Get or create the retriever instance."""
    global retriever
    if retriever is None:
        retriever = GraphCompletionRetrieverWithUserPrompt(
            user_prompt_filename="user_prompt.txt",
            system_prompt_path=str(system_prompt_path),
            top_k=10,
        )
    return retriever


# Request/Response models
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    question: str


@app.on_event("startup")
async def startup_event():
    """Initialize the retriever on startup."""
    get_retriever()
    print("✓ Cognee Agentic API initialized")


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the knowledge graph with a natural language question.
    
    Args:
        request: QueryRequest containing the question
        
    Returns:
        QueryResponse with the answer from the knowledge graph
    """
    try:
        retriever_instance = get_retriever()
        
        # Get completion from knowledge graph
        completions = await retriever_instance.get_completion(
            query=request.question
        )
        
        if not completions or len(completions) == 0:
            raise HTTPException(
                status_code=500,
                detail="No response generated from retriever"
            )
        
        return QueryResponse(
            answer=completions[0],
            question=request.question
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
