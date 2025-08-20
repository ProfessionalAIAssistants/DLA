"""
Test script to check API endpoints
"""
import requests
import sys
import time

def test_pdf_count_endpoint():
    """Test the PDF count endpoint"""
    try:
        response = requests.get('http://localhost:5000/api/pdf-count')
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"PDF count: {data.get('count')}")
            if 'files' in data:
                print(f"Files found: {len(data['files'])}")
                for file in data['files']:
                    print(f"  - {file['name']} ({file['size']} bytes)")
        else:
            print(f"Error: Status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the application is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing PDF count API endpoint...")
    test_pdf_count_endpoint()
