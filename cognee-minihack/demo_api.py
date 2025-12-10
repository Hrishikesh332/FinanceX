"""
Simple demo script to test the agentic API with real queries.
"""
import requests
import json

API_URL = "http://localhost:8000/query"

# Sample questions
questions = [
    "What vendors do we have?",
    "Can you list all transactions from Vendor 2?",
    "What is the total amount we paid to all vendors?"
]

def query_api(question: str):
    """Send a question to the API and print the response."""
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer:")
            print(data['answer'])
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API.")
        print("Make sure the API server is running:")
        print("  cd /Users/hrishikesh/Desktop/Finance/cognee-minihack")
        print("  source .venv/bin/activate")
        print("  python agentic.py")
    except requests.exceptions.Timeout:
        print("Error: Request timed out. The query might be taking too long.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Cognee Agentic API Demo")
    print("=" * 60)
    
    # Test first question only for demo
    query_api(questions[0])
    
    print(f"\n\n{'='*60}")
    print("Demo complete!")
    print(f"{'='*60}")
    print("\nTo test more questions, run the API server:")
    print("  python agentic.py")
    print("\nThen in another terminal:")
    print("  curl -X POST http://localhost:8000/query \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"question\": \"Your question here\"}'")

