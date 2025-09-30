#!/usr/bin/env python3

import json
from xml_validation import lambda_handler

def test_authorizer():
    """Test the XML validation authorizer"""
    
    # Test case 1: Valid XML
    print("Test 1: Valid XML")
    event1 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/mydemoresource/*',
        'body': '<?xml version="1.0"?><root><element>value</element></root>'
    }
    result1 = lambda_handler(event1, {})
    print(f"Result: {json.dumps(result1, indent=2)}")
    print()
    
    # Test case 2: Invalid XML
    print("Test 2: Invalid XML")
    event2 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/mydemoresource/*',
        'body': '<?xml version="1.0"?><root><unclosed-element>value</root>'
    }
    result2 = lambda_handler(event2, {})
    print(f"Result: {json.dumps(result2, indent=2)}")
    print()
    
    # Test case 3: Empty body
    print("Test 3: Empty body")
    event3 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/mydemoresource/*',
        'body': ''
    }
    result3 = lambda_handler(event3, {})
    print(f"Result: {json.dumps(result3, indent=2)}")
    print()
    
    # Test case 4: XML in headers
    print("Test 4: XML in headers")
    event4 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/mydemoresource/*',
        'body': '',
        'headers': {
            'xml-content': '<?xml version="1.0"?><data><item>test</item></data>'
        }
    }
    result4 = lambda_handler(event4, {})
    print(f"Result: {json.dumps(result4, indent=2)}")

if __name__ == "__main__":
    test_authorizer()
