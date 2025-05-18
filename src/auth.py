import jwt
from fastapi import HTTPException, status
from typing import Dict, Optional

# Secret key for JWT token signing and verification
# In a real application, this should be stored securely (e.g., environment variable)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"


def decode_jwt_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode and validate

    Returns:
        The decoded token payload if valid

    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_jwt_token(data: Dict, expires_delta: Optional[int] = None) -> str:
    """
    Create a new JWT token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time in seconds

    Returns:
        The encoded JWT token
    """
    import datetime

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_delta)
        to_encode.update({"exp": expire})

    # Create the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_from_token(token: str) -> Dict:
    """
    Extract user information from a JWT token.

    Args:
        token: The JWT token

    Returns:
        User information extracted from the token
    """
    payload = decode_jwt_token(token)

    # In a real application, you might want to validate the user exists in your database
    # or fetch additional user information

    return {
        "id": payload.get("sub", ""),
        "name": payload.get("name", ""),
        "email": payload.get("email", ""),
    }


def get_user_from_db(email: str, db):
    """
    Get a user from the database by email.

    Args:
        email: The user's email
        db: The database session

    Returns:
        The user if found, None otherwise
    """
    from src.db_models import User

    return db.query(User).filter(User.email == email).first()
