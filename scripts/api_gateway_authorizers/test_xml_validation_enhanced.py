#!/usr/bin/env python3

import json
import base64
import gzip
from xml_validation import lambda_handler

class MockContext:
    def __init__(self):
        self.aws_request_id = "test-12345-67890"

def test_enhanced_authorizer():
    """Test the enhanced XML validation authorizer"""
    
    print("=== Enhanced XML Validation Authorizer Tests ===\n")
    
    # Test case 1: Valid XML with namespace
    print("Test 1: Valid XML with namespace")
    event1 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GetQuote xmlns="http://example.com/stockquote.xsd">
            <symbol>IBM</symbol>
        </GetQuote>
    </soap:Body>
</soap:Envelope>''',
        'headers': {
            'Content-Type': 'text/xml; charset=utf-8',
            'User-Agent': 'Test-Client/1.0'
        },
        'requestContext': {
            'identity': {
                'sourceIp': '203.0.113.12'
            }
        }
    }
    result1 = lambda_handler(event1, MockContext())
    print(f"Result: {json.dumps(result1, indent=2)}")
    print()
    
    # Test case 2: Invalid XML with syntax error
    print("Test 2: Invalid XML with syntax error")
    event2 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': '<?xml version="1.0"?><root><unclosed-element>value</root>',
        'headers': {
            'Content-Type': 'application/xml'
        },
        'requestContext': {
            'identity': {
                'sourceIp': '203.0.113.15'
            }
        }
    }
    result2 = lambda_handler(event2, MockContext())
    print(f"Result: {json.dumps(result2, indent=2)}")
    print()
    
    # Test case 3: Base64 encoded XML
    print("Test 3: Base64 encoded XML")
    xml_content = '<?xml version="1.0"?><data><item id="123">Test Value</item></data>'
    encoded_xml = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
    event3 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': encoded_xml,
        'isBase64Encoded': True,
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    result3 = lambda_handler(event3, MockContext())
    print(f"Result: {json.dumps(result3, indent=2)}")
    print()
    
    # Test case 4: Gzipped XML (simulated)
    print("Test 4: Gzipped XML content")
    xml_data = '<?xml version="1.0"?><large-data>' + '<item>' * 100 + 'content' + '</item>' * 100 + '</large-data>'
    gzipped_data = gzip.compress(xml_data.encode('utf-8'))
    event4 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': base64.b64encode(gzipped_data).decode('utf-8'),
        'isBase64Encoded': True,
        'headers': {
            'Content-Type': 'application/xml',
            'Content-Encoding': 'gzip'
        }
    }
    result4 = lambda_handler(event4, MockContext())
    print(f"Result: {json.dumps(result4, indent=2)}")
    print()
    
    # Test case 5: Potentially dangerous XML with DTD
    print("Test 5: XML with DTD (security test)")
    dangerous_xml = '''<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY test "Hello World">
]>
<root>&test;</root>'''
    event5 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': dangerous_xml,
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    result5 = lambda_handler(event5, MockContext())
    print(f"Result: {json.dumps(result5, indent=2)}")
    print()
    
    # Test case 6: Empty body (should still allow)
    print("Test 6: Empty body")
    event6 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/status/*',
        'body': '',
        'headers': {}
    }
    result6 = lambda_handler(event6, MockContext())
    print(f"Result: {json.dumps(result6, indent=2)}")
    print()
    
    # Test case 7: Very large XML (size limit test)
    print("Test 7: Large XML content")
    large_xml = '<?xml version="1.0"?><data>' + '<item>x</item>' * 10000 + '</data>'
    event7 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/xml/*',
        'body': large_xml,
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    result7 = lambda_handler(event7, MockContext())
    print(f"Result: {json.dumps(result7, indent=2)}")
    print()
    
    # Test case 8: Header-based XML (backward compatibility)
    print("Test 8: XML in headers (backward compatibility)")
    event8 = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/GET/xml/*',
        'body': '',
        'headers': {
            'xml-content': '<?xml version="1.0"?><config><setting>value</setting></config>'
        }
    }
    result8 = lambda_handler(event8, MockContext())
    print(f"Result: {json.dumps(result8, indent=2)}")
    print()

def test_context_consumption():
    """Demonstrate how downstream services can consume the validation context"""
    
    print("=== Context Consumption Example ===\n")
    
    def mock_backend_service(authorizer_context):
        """Mock backend service that processes authorizer context"""
        
        xml_ok = authorizer_context.get('xml_ok', 'false') == 'true'
        xml_severity = authorizer_context.get('xml_severity', 'unknown')
        xml_flags = authorizer_context.get('xml_flags', '').split(',')
        
        if not xml_ok:
            if xml_severity == 'high':
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'High-severity XML validation issues detected',
                        'severity': xml_severity,
                        'flags': xml_flags
                    })
                }
            else:
                # Log warning but continue processing
                print(f"WARNING: XML validation failed with severity {xml_severity}, flags: {xml_flags}")
        
        # Process the valid request
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Request processed successfully',
                'xml_validated': xml_ok,
                'validation_info': {
                    'severity': xml_severity,
                    'root_element': authorizer_context.get('xml_root', ''),
                    'namespace': authorizer_context.get('xml_ns', ''),
                    'size_bytes': authorizer_context.get('xml_size_bytes', '0'),
                    'digest': authorizer_context.get('xml_digest', ''),
                    'parse_time_ms': authorizer_context.get('parse_ms', '0')
                }
            })
        }
    
    # Test with valid XML
    event = {
        'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef123/test/POST/process/*',
        'body': '<?xml version="1.0"?><order><item>laptop</item><quantity>2</quantity></order>',
        'headers': {
            'Content-Type': 'application/xml'
        }
    }
    
    # Get authorizer result
    auth_result = lambda_handler(event, MockContext())
    
    # Simulate API Gateway passing context to backend
    backend_response = mock_backend_service(auth_result['context'])
    
    print("Authorizer Context:")
    print(json.dumps(auth_result['context'], indent=2))
    print("\nBackend Response:")
    print(json.dumps(backend_response, indent=2))

if __name__ == "__main__":
    test_enhanced_authorizer()
    print("\n" + "="*60 + "\n")
    test_context_consumption()