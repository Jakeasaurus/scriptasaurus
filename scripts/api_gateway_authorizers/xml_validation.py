import json
import base64
import gzip
import hashlib
import os
import time
from datetime import datetime
from xml.parsers.expat import ExpatError

# Use defusedxml for security if available, fallback to standard library
try:
    from defusedxml import ElementTree as ET
    USING_DEFUSED_XML = True
except ImportError:
    import xml.etree.ElementTree as ET
    USING_DEFUSED_XML = False


# Configuration from environment variables
CONFIG = {
    'MAX_XML_BYTES': int(os.environ.get('AUTHZ_MAX_XML_BYTES', '524288')),  # 512KB
    'MAX_CONTEXT_BYTES': int(os.environ.get('AUTHZ_MAX_CONTEXT_BYTES', '3000')),
    'SNIPPET_BYTES': int(os.environ.get('AUTHZ_TRUNCATED_SNIPPET_BYTES', '256')),
    'DEBUG_SAMPLING': float(os.environ.get('AUTHZ_DEBUG_SAMPLING', '0.05')),
    'ALLOW_GZIP': os.environ.get('AUTHZ_ALLOW_GZIP', 'true').lower() == 'true',
    'HASH_ALGO': os.environ.get('AUTHZ_HASH_ALGO', 'sha256')
}

def decode_body(body, is_base64_encoded=False, headers=None):
    """
    Safely decode body with size limits and decompression
    Returns tuple: (decoded_body, actual_size, flags)
    """
    if not body:
        return "", 0, ["empty_body"]
    
    flags = []
    
    try:
        # Base64 decode if needed
        if is_base64_encoded:
            body = base64.b64decode(body)
            flags.append("base64_decoded")
        
        # Handle bytes vs string
        if isinstance(body, str):
            body_bytes = body.encode('utf-8')
        else:
            body_bytes = body
            
        # Check if gzipped and decompress
        if CONFIG['ALLOW_GZIP'] and len(body_bytes) >= 2 and body_bytes[:2] == b'\x1f\x8b':
            try:
                # Decompress with size limit
                body_bytes = gzip.decompress(body_bytes)
                flags.append("gzip_decompressed")
            except Exception as e:
                flags.append(f"gzip_error:{str(e)[:50]}")
        
        # Enforce size limit
        actual_size = len(body_bytes)
        if actual_size > CONFIG['MAX_XML_BYTES']:
            flags.append("oversized")
            return body_bytes.decode('utf-8', errors='replace')[:CONFIG['MAX_XML_BYTES']], actual_size, flags
        
        return body_bytes.decode('utf-8', errors='replace'), actual_size, flags
        
    except Exception as e:
        flags.append(f"decode_error:{str(e)[:50]}")
        return str(body)[:CONFIG['MAX_XML_BYTES']], len(str(body)), flags

def create_digest(content):
    """
    Create a hash digest of the content
    """
    hasher = hashlib.new(CONFIG['HASH_ALGO'])
    hasher.update(content.encode('utf-8') if isinstance(content, str) else content)
    return hasher.hexdigest()[:16]  # First 16 chars

def sanitize_snippet(content, max_bytes=None):
    """
    Create a safe snippet for logging
    """
    if not content:
        return ""
    
    max_bytes = max_bytes or CONFIG['SNIPPET_BYTES']
    
    # Remove control characters except newlines and tabs
    safe_chars = []
    for char in content[:max_bytes]:
        if ord(char) >= 32 or char in '\n\t':
            safe_chars.append(char)
        else:
            safe_chars.append('�')  # Replacement character
    
    snippet = ''.join(safe_chars)
    if len(content) > max_bytes:
        snippet += "...[truncated]"
    
    return snippet

def validate_xml_enhanced(xml_content, request_id=None):
    """
    Enhanced XML validation with security checks and detailed reporting
    Returns dict with validation results
    """
    start_time = time.time()
    
    result = {
        'is_valid': False,
        'severity': 'none',
        'flags': [],
        'errors': [],
        'root_element': '',
        'namespace': '',
        'size_bytes': len(xml_content) if xml_content else 0,
        'digest': '',
        'snippet': '',
        'parse_time_ms': 0
    }
    
    if not xml_content or not xml_content.strip():
        result['errors'].append({'category': 'empty', 'message': 'Empty XML body'})
        result['severity'] = 'low'
        return result
    
    # Create digest and snippet
    result['digest'] = create_digest(xml_content)
    result['snippet'] = sanitize_snippet(xml_content)
    
    # Pre-scan for dangerous constructs
    dangerous_patterns = ['<!DOCTYPE', '<!ENTITY', '&', 'SYSTEM', 'PUBLIC']
    for pattern in dangerous_patterns:
        if pattern in xml_content:
            result['flags'].append(f'dangerous_{pattern.lower().replace("<!", "").replace("&", "entity")}')
            result['severity'] = 'high'
    
    # Check for excessive nesting (simple heuristic)
    max_depth = xml_content.count('<') - xml_content.count('</')
    if max_depth > 50:
        result['flags'].append('deep_nesting')
        result['severity'] = 'medium' if result['severity'] != 'high' else 'high'
    
    try:
        # Parse XML
        if USING_DEFUSED_XML:
            # defusedxml provides better security
            root = ET.fromstring(xml_content)
        else:
            # Standard library parsing
            root = ET.fromstring(xml_content)
        
        # Extract metadata
        result['is_valid'] = True
        result['root_element'] = root.tag
        
        # Extract namespace if present
        if root.tag.startswith('{'):
            result['namespace'] = root.tag[1:root.tag.find('}')]
        
        if result['severity'] == 'none':
            result['severity'] = 'none'
            
    except ET.ParseError as e:
        result['errors'].append({
            'category': 'syntax',
            'message': f'XML Parse Error: {str(e)}',
            'details': str(e)
        })
        result['severity'] = 'medium' if result['severity'] != 'high' else 'high'
    except ExpatError as e:
        result['errors'].append({
            'category': 'syntax', 
            'message': f'XML Parsing Error: {str(e)}',
            'details': str(e)
        })
        result['severity'] = 'medium' if result['severity'] != 'high' else 'high'
    except Exception as e:
        result['errors'].append({
            'category': 'unexpected',
            'message': f'Unexpected validation error: {str(e)}',
            'details': str(e)
        })
        result['severity'] = 'medium' if result['severity'] != 'high' else 'high'
    
    result['parse_time_ms'] = int((time.time() - start_time) * 1000)
    return result


def build_context_data(validation_result, request_info, decode_flags=None):
    """
    Build context data for API Gateway with size limits
    """
    context = {
        'xml_ok': str(validation_result['is_valid']).lower(),
        'xml_size_bytes': str(validation_result['size_bytes']),
        'xml_root': validation_result['root_element'],
        'xml_ns': validation_result['namespace'],
        'xml_severity': validation_result['severity'],
        'xml_flags': ','.join(validation_result['flags'] + (decode_flags or [])),
        'xml_digest': validation_result['digest'],
        'xml_snip': validation_result['snippet'][:100],  # Limit snippet size
        'parse_ms': str(validation_result['parse_time_ms']),
        'debug_id': request_info.get('request_id', 'unknown')[:16]
    }
    
    # Pack detailed validation data as JSON
    vctx = {
        'validation': validation_result,
        'request_info': request_info,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    try:
        vctx_json = json.dumps(vctx, separators=(',', ':'))
        if len(vctx_json) <= CONFIG['MAX_CONTEXT_BYTES']:
            context['vctx'] = vctx_json
        else:
            # Truncate if too large
            context['vctx'] = vctx_json[:CONFIG['MAX_CONTEXT_BYTES'] - 20] + '...[truncated]'
            context['xml_flags'] += ',vctx_truncated'
    except Exception:
        context['xml_flags'] += ',vctx_error'
    
    return context

def generate_policy(effect, resource, context_data=None):
    """
    Generate IAM policy document for API Gateway
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": resource
            }
        ]
    }
    
    response = {
        "principalId": "xml-validator",
        "policyDocument": policy
    }
    
    if context_data:
        response["context"] = context_data
    
    return response


def log_request(request_info, validation_result, decode_flags=None, debug=False):
    """
    Structured logging with redaction and sampling
    """
    import random
    
    # Always log basic info
    log_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': 'INFO',
        'authorizer': 'xml-validator',
        'request_id': request_info.get('request_id', 'unknown'),
        'source_ip': request_info.get('source_ip', 'unknown'),
        'user_agent': request_info.get('user_agent', 'unknown')[:100],
        'content_type': request_info.get('content_type', 'unknown'),
        'xml_ok': validation_result['is_valid'],
        'xml_size': validation_result['size_bytes'],
        'xml_severity': validation_result['severity'],
        'xml_flags': ','.join(validation_result['flags'] + (decode_flags or [])),
        'xml_digest': validation_result['digest'],
        'parse_ms': validation_result['parse_time_ms'],
        'error_count': len(validation_result['errors']),
        'defused_xml': USING_DEFUSED_XML
    }
    
    print(json.dumps(log_data, separators=(',', ':')))
    
    # Debug logging with sampling
    if debug and random.random() < CONFIG['DEBUG_SAMPLING']:
        debug_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': 'DEBUG',
            'request_id': request_info.get('request_id', 'unknown'),
            'xml_snippet': validation_result['snippet'],
            'errors': validation_result['errors'][:5],  # Limit error details
            'decode_flags': decode_flags or []
        }
        print(json.dumps(debug_data, separators=(',', ':')))

def lambda_handler(event, context):
    """
    Enhanced Lambda authorizer for API Gateway that validates XML content
    Always defaults to ALLOW with comprehensive validation context
    Supports both policy-based and simple authorizer response formats
    """
    start_time = time.time()
    
    try:
        # Detect authorizer type based on event structure
        is_simple_authorizer = 'type' in event and event.get('type') == 'TOKEN'
        
        # Extract request information - handle both formats
        if context and hasattr(context, 'aws_request_id'):
            request_id = context.aws_request_id
        else:
            request_id = 'local-test'
            
        request_info = {
            'request_id': request_id,
            'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown'),
            'user_agent': event.get('headers', {}).get('User-Agent', 'unknown'),
            'content_type': event.get('headers', {}).get('Content-Type', 'unknown'),
            'method_arn': event.get('methodArn', event.get('resource', ''))
        }
        
        # Decode body with safety checks
        raw_body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        headers = event.get('headers', {})
        
        # If no body, check headers for XML content (backward compatibility)
        if not raw_body:
            raw_body = headers.get('xml-content', '')
        
        xml_content, actual_size, decode_flags = decode_body(raw_body, is_base64, headers)
        
        # Enhanced XML validation
        validation_result = validate_xml_enhanced(xml_content, request_info['request_id'])
        
        # Build enriched context for downstream services
        context_data = build_context_data(validation_result, request_info, decode_flags)
        
        # Log the request (structured logging)
        log_request(request_info, validation_result, decode_flags, debug=True)
        
        # Return appropriate response format
        if is_simple_authorizer:
            # Simple authorizer response
            return {
                "isAuthorized": True,  # Always allow
                "context": {
                    "validationStatus": "passed" if validation_result['is_valid'] else "failed",
                    "xmlParsed": str(validation_result['is_valid']).lower(),
                    "xmlSeverity": validation_result['severity'],
                    "xmlFlags": ','.join(validation_result['flags'] + (decode_flags or [])),
                    "xmlDigest": validation_result['digest'],
                    "message": "Valid XML" if validation_result['is_valid'] else (
                        validation_result['errors'][0]['message'] if validation_result['errors'] 
                        else "XML validation failed"
                    )
                }
            }
        else:
            # Policy-based authorizer response (default)
            response = generate_policy("Allow", request_info['method_arn'], context_data)
            
            # Add usage identifier based on validation status
            if validation_result['is_valid']:
                response["usageIdentifierKey"] = "xml-validated-request"
            else:
                response["usageIdentifierKey"] = "xml-validation-failed"
            
            return response
        
    except Exception as e:
        # Emergency fallback - always allow with error context
        error_message = str(e)[:200]
        
        # Simple error logging
        error_log = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': 'ERROR',
            'authorizer': 'xml-validator',
            'request_id': request_info.get('request_id', 'unknown') if 'request_info' in locals() else 'unknown',
            'error': error_message,
            'event_keys': list(event.keys()) if event else []
        }
        print(json.dumps(error_log, separators=(',', ':')))
        
        # Detect response type for error fallback
        is_simple_authorizer = 'type' in event and event.get('type') == 'TOKEN'
        
        if is_simple_authorizer:
            # Simple authorizer error response
            return {
                "isAuthorized": True,  # Still allow
                "context": {
                    "validationStatus": "error",
                    "xmlParsed": "false",
                    "error": f"Authorizer error: {error_message}",
                    "allowedByDefault": "true"
                }
            }
        else:
            # Policy-based error response
            method_arn = event.get('methodArn', event.get('resource', '*'))
            return {
                "principalId": "xml-validator",
                "policyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": method_arn
                    }]
                },
                "context": {
                    "validationStatus": "error",
                    "xmlParsed": "false",
                    "error": f"Authorizer error: {error_message}",
                    "allowedByDefault": "true"
                },
                "usageIdentifierKey": "xml-authorizer-error"
            }


# Backward compatibility function
def validate_xml(xml_string):
    """
    Backward compatible XML validation function
    Returns tuple: (is_valid, error_message)
    """
    result = validate_xml_enhanced(xml_string)
    
    if result['is_valid']:
        return True, "Valid XML"
    elif result['errors']:
        return False, result['errors'][0]['message']
    else:
        return False, "XML validation failed"

# Optional: Add XSD validation function
def validate_xml_with_xsd(xml_string, xsd_string=None):
    """
    Validate XML against XSD schema (requires lxml library)
    This is a placeholder - you'd need to install lxml for full XSD validation
    """
    try:
        from lxml import etree
        
        if xsd_string:
            schema_doc = etree.fromstring(xsd_string)
            schema = etree.XMLSchema(schema_doc)
            xml_doc = etree.fromstring(xml_string)
            
            if schema.validate(xml_doc):
                return True, "Valid against XSD"
            else:
                return False, f"XSD Validation failed: {schema.error_log}"
        else:
            # Just check well-formedness without schema
            etree.fromstring(xml_string)
            return True, "Well-formed XML"
            
    except ImportError:
        # Fallback to basic XML validation if lxml is not available
        return validate_xml(xml_string)
    except Exception as e:
        return False, f"XSD Validation error: {str(e)}"
