# -*- coding: utf-8 -*-
"""
Security utilities - Input validation, sanitization, and security helpers.
"""

import re
import html
import logging
from functools import wraps
from flask import request, jsonify, session
from typing import Optional, Dict, Any

# Try to import bleach, fall back to basic sanitization
try:
    import bleach
    HAS_BLEACH = True
except ImportError:
    HAS_BLEACH = False
    logging.warning("bleach not installed, using basic sanitization")


# ============= INPUT SANITIZATION =============

def sanitize_input(text: str, strip: bool = True) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text: Input text to sanitize
        strip: Whether to strip whitespace
    
    Returns:
        Sanitized text
    """
    if text is None:
        return ""
    
    text = str(text)
    
    if HAS_BLEACH:
        # Use bleach for proper HTML sanitization
        text = bleach.clean(text, tags=[], strip=strip)
    else:
        # Basic HTML entity escaping
        text = html.escape(text)
    
    if strip:
        text = text.strip()
    
    return text


def sanitize_html(text: str, allowed_tags: list = None) -> str:
    """
    Sanitize HTML while allowing specific tags.
    
    Args:
        text: HTML text to sanitize
        allowed_tags: List of allowed HTML tags
    
    Returns:
        Sanitized HTML
    """
    if text is None:
        return ""
    
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'br']
    
    if HAS_BLEACH:
        return bleach.clean(text, tags=allowed_tags, strip=True)
    else:
        # Basic: strip all HTML for safety
        return html.escape(text)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Safe filename
    """
    if not filename:
        return "unnamed"
    
    # Remove directory path components
    filename = filename.replace('\\', '/').split('/')[-1]
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Limit length
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:195] + ('.' + ext if ext else '')
    
    return filename or "unnamed"


def sanitize_dict(data: Dict[str, Any], keys_to_sanitize: list = None) -> Dict[str, Any]:
    """
    Sanitize all string values in a dictionary.
    
    Args:
        data: Dictionary to sanitize
        keys_to_sanitize: Specific keys to sanitize (None = all)
    
    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data
    
    result = {}
    for key, value in data.items():
        if keys_to_sanitize is None or key in keys_to_sanitize:
            if isinstance(value, str):
                result[key] = sanitize_input(value)
            elif isinstance(value, dict):
                result[key] = sanitize_dict(value, keys_to_sanitize)
            elif isinstance(value, list):
                result[key] = [
                    sanitize_input(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result


# ============= INPUT VALIDATION =============

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str, min_length: int = 6) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum required length
    
    Returns:
        dict: {valid: bool, errors: list}
    """
    errors = []
    
    if not password:
        return {'valid': False, 'errors': ['Şifre gerekli']}
    
    if len(password) < min_length:
        errors.append(f'Şifre en az {min_length} karakter olmalı')
    
    # Note: User requested only 6 char minimum, no special requirements
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'strength': 'weak' if len(password) < 8 else 'medium' if len(password) < 12 else 'strong'
    }


def validate_barcode(barcode: str) -> bool:
    """Validate barcode format (EAN-13 or similar)"""
    if not barcode:
        return False
    
    # Allow numeric barcodes 8-14 digits
    return bool(re.match(r'^\d{8,14}$', barcode))


def validate_price(price: Any) -> Optional[float]:
    """
    Validate and convert price to float.
    
    Args:
        price: Price value (can be string or number)
    
    Returns:
        float or None if invalid
    """
    if price is None:
        return None
    
    try:
        # Handle Turkish number format (comma as decimal)
        if isinstance(price, str):
            price = price.replace(',', '.').strip()
        
        value = float(price)
        
        if value < 0:
            return None
        
        return round(value, 2)
    except (ValueError, TypeError):
        return None


def validate_json_request(required_fields: list = None) -> Dict[str, Any]:
    """
    Validate JSON request and return sanitized data.
    
    Args:
        required_fields: List of required field names
    
    Returns:
        dict: {valid: bool, data: dict, errors: list}
    """
    required_fields = required_fields or []
    errors = []
    
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        data = None
    
    if not data:
        return {
            'valid': False,
            'data': {},
            'errors': ['Geçersiz JSON verisi']
        }
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            errors.append(f'{field} alanı gerekli')
    
    # Sanitize all string values
    sanitized_data = sanitize_dict(data)
    
    return {
        'valid': len(errors) == 0,
        'data': sanitized_data,
        'errors': errors
    }


# ============= SECURITY DECORATORS =============

def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        return f(*args, **kwargs)
    return decorated_function


def validate_request(*required_fields):
    """
    Decorator to validate request JSON and required fields.
    
    Usage:
        @validate_request('email', 'password')
        def login(validated_data):
            email = validated_data['email']
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            result = validate_json_request(list(required_fields))
            
            if not result['valid']:
                return jsonify({
                    'success': False,
                    'errors': result['errors']
                }), 400
            
            # Pass validated data as first argument
            return f(result['data'], *args, **kwargs)
        return decorated_function
    return decorator


# ============= RATE LIMIT HELPERS =============

def get_remote_address():
    """Get client IP address, considering proxies"""
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        # Get first IP in chain (original client)
        return forwarded.split(',')[0].strip()
    
    return request.remote_addr or '127.0.0.1'


def get_rate_limit_key():
    """Get rate limit key based on user or IP"""
    # If user is logged in, use user ID
    user_id = session.get('user_id')
    if user_id:
        return f"user:{user_id}"
    
    # Otherwise use IP address
    return f"ip:{get_remote_address()}"


# ============= SECURITY CHECKS =============

def check_sql_injection(text: str) -> bool:
    """
    Check if text contains potential SQL injection patterns.
    
    Returns True if suspicious patterns found.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    suspicious_patterns = [
        "' or '", "' and '", "'; drop", "; drop",
        "union select", "1=1", "1 = 1",
        "exec(", "execute(", "--", "/*", "*/"
    ]
    
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            logging.warning(f"Potential SQL injection detected: {text[:50]}...")
            return True
    
    return False


def check_xss_patterns(text: str) -> bool:
    """
    Check if text contains potential XSS patterns.
    
    Returns True if suspicious patterns found.
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    suspicious_patterns = [
        "<script", "javascript:", "onerror=", "onload=",
        "onclick=", "onmouseover=", "onfocus=", "onblur=",
        "eval(", "document.cookie", "document.write"
    ]
    
    for pattern in suspicious_patterns:
        if pattern in text_lower:
            logging.warning(f"Potential XSS detected: {text[:50]}...")
            return True
    
    return False


def is_safe_input(text: str) -> bool:
    """
    Check if input is safe (no SQL injection or XSS).
    
    Returns True if safe.
    """
    if not text:
        return True
    
    return not check_sql_injection(text) and not check_xss_patterns(text)


# ============= CSRF HELPERS =============

def generate_csrf_token() -> str:
    """Generate a CSRF token for the session"""
    import secrets
    
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    
    return session['csrf_token']


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token against session"""
    if not token:
        return False
    
    session_token = session.get('csrf_token')
    if not session_token:
        return False
    
    # Constant-time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(token, session_token)

