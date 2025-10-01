"""
Authentication middleware for eCademy API.

Simple API Key authentication using Bearer tokens.
Configure API_KEYS in .env (comma-separated for multiple keys).
"""

import os
import secrets
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


def get_api_keys() -> list[str]:
    """
    Get list of valid API keys from environment variable.

    Returns:
        List of valid API key strings.
    """
    keys_str = os.getenv("API_KEYS", "")
    if not keys_str:
        return []
    return [key.strip() for key in keys_str.split(",") if key.strip()]


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify API key from Authorization header.

    Args:
        credentials: HTTP Authorization credentials with Bearer token.

    Returns:
        The verified API key.

    Raises:
        HTTPException: If API key is invalid or missing.
    """
    valid_keys = get_api_keys()

    # If no API keys configured, allow access (development mode)
    if not valid_keys:
        return "dev-mode-no-auth"

    token = credentials.credentials

    # Constant-time comparison to prevent timing attacks
    if any(secrets.compare_digest(token, valid_key) for valid_key in valid_keys):
        return token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


def optional_verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """
    Optional API key verification (for endpoints that can work with or without auth).

    Args:
        credentials: Optional HTTP Authorization credentials.

    Returns:
        The API key if provided and valid, None otherwise.
    """
    if credentials is None:
        return None

    try:
        return verify_api_key(credentials)
    except HTTPException:
        return None


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        A 32-character hex string suitable for use as an API key.
    """
    return secrets.token_hex(32)
