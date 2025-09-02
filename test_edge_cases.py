#!/usr/bin/env python3
"""
Test script to demonstrate edge case handling in the ServiceNow Ticket Agent
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_missing_required_fields():
    """Test handling of tickets with missing required fields"""
    print("=== Testing Missing Required Fields ===")
    
    # Create a ticket with missing required fields
    invalid_ticket = {
        "number": 999,
        # Missing title, description, created_time, state
        "priority": "P3",
        "owner": "test_user"
    }
    
    print(f"Invalid ticket data: {json.dumps(invalid_ticket, indent=2)}")
    print("Expected: Validation error for missing required fields")
    print()

def test_wrong_data_types():
    """Test handling of wrong data types"""
    print("=== Testing Wrong Data Types ===")
    
    # Test with string ticket number instead of int
    try:
        response = requests.get(f"{BASE_URL}/api/ticket/abc")
        print(f"String ticket number response: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test with invalid limit parameter
    try:
        response = requests.get(f"{BASE_URL}/api/tickets?limit=invalid")
        print(f"Invalid limit response: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

def test_oversized_payloads():
    """Test handling of oversized payloads"""
    print("=== Testing Oversized Payloads ===")
    
    # Create a ticket with oversized description
    oversized_description = "A" * 15000  # 15k characters
    
    print(f"Description length: {len(oversized_description)} characters")
    print("Expected: Description should be truncated to 10,000 characters")
    print()

def test_duplicate_requests():
    """Test handling of duplicate requests"""
    print("=== Testing Duplicate Requests ===")
    
    # First, get a valid ticket number
    try:
        response = requests.get(f"{BASE_URL}/api/tickets?limit=1")
        if response.status_code == 200:
            tickets = response.json().get("tickets", [])
            if tickets:
                ticket_number = tickets[0]["number"]
                print(f"Testing with ticket #{ticket_number}")
                
                # Process the same ticket twice
                print("Processing ticket first time...")
                response1 = requests.post(f"{BASE_URL}/api/process-ticket", params={"ticket_number": ticket_number})
                print(f"First request status: {response1.status_code}")
                
                print("Processing ticket second time...")
                response2 = requests.post(f"{BASE_URL}/api/process-ticket", params={"ticket_number": ticket_number})
                print(f"Second request status: {response2.status_code}")
                print(f"Second request response: {response2.json()}")
                
                # Check validation status
                status_response = requests.get(f"{BASE_URL}/api/validation/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Processed tickets: {status_data.get('processed_tickets', [])}")
                
    except Exception as e:
        print(f"Error: {e}")
    
    print()

def test_validation_status():
    """Test validation status endpoint"""
    print("=== Testing Validation Status ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/validation/status")
        if response.status_code == 200:
            status_data = response.json()
            print("Validation Configuration:")
            config = status_data.get("validation_config", {})
            for key, value in config.items():
                print(f"  {key}: {value}")
            print(f"Processed tickets: {status_data.get('processed_tickets', [])}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

def test_clear_processed_tickets():
    """Test clearing processed tickets"""
    print("=== Testing Clear Processed Tickets ===")
    
    try:
        response = requests.post(f"{BASE_URL}/api/validation/clear-processed")
        if response.status_code == 200:
            print("Successfully cleared processed tickets")
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()

def main():
    """Run all edge case tests"""
    print("ServiceNow Ticket Agent - Edge Case Testing")
    print("=" * 50)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("Warning: Server may not be running properly")
            print()
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Please make sure the server is running on http://localhost:8000")
        print()
        return
    
    # Run tests
    test_missing_required_fields()
    test_wrong_data_types()
    test_oversized_payloads()
    test_duplicate_requests()
    test_validation_status()
    test_clear_processed_tickets()
    
    print("Edge case testing completed!")

if __name__ == "__main__":
    main()
