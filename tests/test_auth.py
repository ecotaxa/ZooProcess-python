import pytest
import jwt
import datetime
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from src.auth import (
    create_jwt_token,
    decode_jwt_token,
    get_user_from_token,
    SECRET_KEY,
    ALGORITHM,
)


def test_create_jwt_token():
    """Test that create_jwt_token creates a valid JWT token with the expected data"""
    # Test data
    test_data = {
        "sub": "123456789",
        "name": "Test User",
        "email": "test@example.com",
    }

    # Create token without expiration
    token = create_jwt_token(test_data)

    # Decode the token and verify its contents
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    # Check that the decoded token contains the test data
    assert decoded["sub"] == test_data["sub"]
    assert decoded["name"] == test_data["name"]
    assert decoded["email"] == test_data["email"]

    # Test with expiration
    expires_delta = 3600  # 1 hour
    token_with_exp = create_jwt_token(test_data, expires_delta=expires_delta)

    # Decode and verify
    decoded_with_exp = jwt.decode(token_with_exp, SECRET_KEY, algorithms=[ALGORITHM])

    # Check that expiration is set
    assert "exp" in decoded_with_exp


def test_decode_jwt_token_valid():
    """Test that decode_jwt_token correctly decodes a valid token"""
    # Create a valid token
    payload = {"sub": "123456789", "name": "Test User"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Decode the token
    decoded = decode_jwt_token(token)

    # Check that the decoded token matches the original payload
    assert decoded["sub"] == payload["sub"]
    assert decoded["name"] == payload["name"]


def test_decode_jwt_token_expired():
    """Test that decode_jwt_token raises an exception for an expired token"""
    # Create an expired token
    payload = {
        "sub": "123456789",
        "exp": datetime.datetime.utcnow() - datetime.timedelta(seconds=1),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Attempt to decode the expired token
    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(token)

    # Check that the exception has the correct status code and detail
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"


def test_decode_jwt_token_invalid():
    """Test that decode_jwt_token raises an exception for an invalid token"""
    # Create an invalid token (wrong signature)
    payload = {"sub": "123456789"}
    token = jwt.encode(payload, "wrong-secret", algorithm=ALGORITHM)

    # Attempt to decode the invalid token
    with pytest.raises(HTTPException) as exc_info:
        decode_jwt_token(token)

    # Check that the exception has the correct status code and detail
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token"


def test_get_user_from_token():
    """Test that get_user_from_token extracts user information correctly"""
    # Create a token with user information
    user_data = {
        "sub": "123456789",
        "name": "Test User",
        "email": "test@example.com",
    }
    token = jwt.encode(user_data, SECRET_KEY, algorithm=ALGORITHM)

    # Extract user information from the token
    user = get_user_from_token(token)

    # Check that the extracted user information matches the original data
    assert user["id"] == user_data["sub"]
    assert user["name"] == user_data["name"]
    assert user["email"] == user_data["email"]
