"""
Test script for the data API.
"""
import requests
import json

API_BASE = "http://localhost:8001"

def test_invoices():
    """Test the /invoices endpoint."""
    print("\nTesting /invoices endpoint...")
    try:
        response = requests.get(f"{API_BASE}/invoices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Retrieved {len(data)} invoices")
            if data:
                print(f"  Sample invoice: {data[0]}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the server is running:")
        print("  cd services && python data.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_transactions():
    """Test the /transactions endpoint."""
    print("\nTesting /transactions endpoint...")
    try:
        response = requests.get(f"{API_BASE}/transactions", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Retrieved {len(data)} transactions")
            if data:
                print(f"  Sample transaction: {data[0]}")
            return True
        else:
            print(f"✗ Error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure the server is running:")
        print("  cd services && python data.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data API")
    print("=" * 60)
    
    invoices_ok = test_invoices()
    transactions_ok = test_transactions()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"  Invoices: {'✓' if invoices_ok else '✗'}")
    print(f"  Transactions: {'✓' if transactions_ok else '✗'}")
    print("=" * 60)
    
    if invoices_ok and transactions_ok:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")

