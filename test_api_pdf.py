#!/usr/bin/env python3
"""
Test which PDF library the API server is using
"""
import requests
import json

# Upload a small test file to see extraction results
test_content = "Testing PDF library detection"
files = {'file': ('test.txt', test_content.encode(), 'text/plain')}

try:
    response = requests.post("http://localhost:8003/api/process/upload", files=files)
    result = response.json()
    print(f"Upload test result: {result}")
    
    # Check the actual extraction by searching the logs or checking the database
    # We can't directly test PDF since we need a PDF file, but we can check config
    
except Exception as e:
    print(f"Error testing API: {e}")