"""
Test script for the agentic.py FastAPI service.
This script tests the query endpoint to ensure it works correctly.
"""
import asyncio
import sys
import requests
import signal
from agentic import app, get_retriever, QueryRequest, QueryResponse
from fastapi.testclient import TestClient


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


async def test_retriever_initialization():
    """Test that the retriever can be initialized."""
    print("Testing retriever initialization...")
    try:
        retriever = get_retriever()
        print("✓ Retriever initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize retriever: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint():
    """Test the /query endpoint using FastAPI TestClient."""
    print("\nTesting /query endpoint...")
    
    # Check if Ollama is running first
    if not check_ollama_running():
        print("⚠ Ollama is not running. Skipping actual query test.")
        print("  To test the full functionality, start Ollama first:")
        print("  - Install Ollama from https://ollama.com/")
        print("  - Register models: cd models && ollama create nomic-embed-text -f nomic-embed-text/Modelfile")
        print("  - Then run: ollama serve")
        return None  # Return None to indicate skipped
    
    client = TestClient(app)
    
    # Test with a sample question
    test_question = "What vendors do we have?"
    
    try:
        print(f"  Sending query: '{test_question}'")
        print("  (This may take a while as it queries the knowledge graph and LLM)...")
        
        response = client.post(
            "/query",
            json={"question": test_question}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ API endpoint responded successfully")
            print(f"  Question: {data.get('question')}")
            answer = data.get('answer', '')
            print(f"  Answer: {answer[:200]}...")  # First 200 chars
            if len(answer) > 200:
                print(f"  (Answer truncated, total length: {len(answer)} chars)")
            return True
        else:
            print(f"✗ API endpoint returned error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            print("✗ Request timed out (this might indicate Ollama is not responding)")
            return False
        print(f"✗ Failed to test API endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_request_response_models():
    """Test that the request/response models are correctly defined."""
    print("\nTesting request/response models...")
    
    try:
        # Test QueryRequest
        request = QueryRequest(question="Test question")
        assert request.question == "Test question"
        print("✓ QueryRequest model works correctly")
        
        # Test QueryResponse
        response = QueryResponse(answer="Test answer", question="Test question")
        assert response.answer == "Test answer"
        assert response.question == "Test question"
        print("✓ QueryResponse model works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Cognee Agentic API")
    print("=" * 60)
    
    # Test 1: Request/Response models
    model_test = test_request_response_models()
    
    # Test 2: Retriever initialization
    retriever_test = await test_retriever_initialization()
    
    # Test 3: API endpoint (only if retriever works)
    if retriever_test:
        api_test = test_api_endpoint()
    else:
        print("\n⚠ Skipping API endpoint test (retriever initialization failed)")
        api_test = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Models: {'✓' if model_test else '✗'}")
    print(f"  Retriever: {'✓' if retriever_test else '✗'}")
    if api_test is None:
        print(f"  API Endpoint: ⚠ Skipped (Ollama not running)")
    else:
        print(f"  API Endpoint: {'✓' if api_test else '✗'}")
    print("=" * 60)
    
    # Check if all non-skipped tests passed
    tests_passed = [model_test, retriever_test]
    if api_test is not None:
        tests_passed.append(api_test)
    
    if all(tests_passed):
        print("\n✓ All tests passed!")
        if api_test is None:
            print("  (Note: Full API test was skipped - start Ollama to test complete functionality)")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

