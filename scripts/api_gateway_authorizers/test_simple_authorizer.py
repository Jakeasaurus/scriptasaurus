#!/usr/bin/env python3

import json
from xml_validation import lambda_handler

class MockContext:
    def __init__(self):
        self.aws_request_id = "test-simple-auth-12345"

def test_simple_authorizer_format():
    """Test the simple authorizer format (isAuthorized response)"""
    
    print("=== Simple Authorizer Format Tests (for Lambda Console) ===\n")
    
    # Test case 1: Valid XML with simple authorizer
    print("Test 1: Valid XML - Simple Authorizer")
    event1 = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer token123',
        'resource': '/xml/validate',
        'body': '<?xml version="1.0"?><order><item>laptop</item><quantity>2</quantity></order>',
        'headers': {
            'Content-Type': 'application/xml',
            'User-Agent': 'PostmanRuntime/7.29.0'
        }
    }
    result1 = lambda_handler(event1, MockContext())
    print(f"Result: {json.dumps(result1, indent=2)}")
    print()
    
    # Test case 2: Invalid XML with simple authorizer
    print("Test 2: Invalid XML - Simple Authorizer") 
    event2 = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer token123',
        'resource': '/xml/validate',
        'body': '<?xml version="1.0"?><order><unclosed-item>laptop</order>',
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    result2 = lambda_handler(event2, MockContext())
    print(f"Result: {json.dumps(result2, indent=2)}")
    print()
    
    # Test case 3: Dangerous XML with simple authorizer
    print("Test 3: Dangerous XML - Simple Authorizer")
    dangerous_xml = '''<?xml version="1.0"?>
<!DOCTYPE order [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<order>&xxe;</order>'''
    
    event3 = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer token123',
        'resource': '/xml/validate',
        'body': dangerous_xml,
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    result3 = lambda_handler(event3, MockContext())
    print(f"Result: {json.dumps(result3, indent=2)}")
    print()
    
    # Test case 4: Empty body with simple authorizer
    print("Test 4: Empty Body - Simple Authorizer")
    event4 = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer token123',
        'resource': '/xml/validate',
        'body': '',
        'headers': {}
    }
    result4 = lambda_handler(event4, MockContext())
    print(f"Result: {json.dumps(result4, indent=2)}")
    print()

def test_policy_authorizer_format():
    """Test the policy authorizer format (traditional)"""
    
    print("=== Policy Authorizer Format Tests (for API Gateway Integration) ===\n")
    
    # Test case: Valid XML with policy authorizer
    print("Test 1: Valid XML - Policy Authorizer")
    event1 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': '<?xml version="1.0"?><order><item>laptop</item><quantity>2</quantity></order>',
        'headers': {
            'Content-Type': 'application/xml',
            'User-Agent': 'PostmanRuntime/7.29.0'
        },
        'requestContext': {
            'identity': {
                'sourceIp': '203.0.113.20'
            }
        }
    }
    result1 = lambda_handler(event1, MockContext())
    print(f"Result: {json.dumps(result1, indent=2)}")
    print()

def test_error_handling():
    """Test error handling in both formats"""
    
    print("=== Error Handling Tests ===\n")
    
    # Test case 1: Error in simple authorizer
    print("Test 1: Forced Error - Simple Authorizer")
    event1 = {
        'type': 'TOKEN',
        'authorizationToken': 'Bearer token123',
        # Missing required fields to force an error
        'body': None  # This should cause an error in processing
    }
    result1 = lambda_handler(event1, MockContext())
    print(f"Result: {json.dumps(result1, indent=2)}")
    print()

if __name__ == "__main__":
    test_simple_authorizer_format()
    print("\n" + "="*60 + "\n")
    test_policy_authorizer_format()
    print("\n" + "="*60 + "\n")
    test_error_handling()