import jwt
import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import Dict, Optional
from starlette.requests import Request

from local_DB.db_dependencies import get_db
from config_rdr import config


class CustomHTTPBearer(HTTPBearer):
    """
    Custom HTTP Bearer token authentication that returns 401 instead of 403 when no token is provided.
    """

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        authorization = request.headers.get("Authorization")
        scheme, credentials = self.get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)

    def get_authorization_scheme_param(self, authorization_header: str):
        if not authorization_header:
            return "", ""
        scheme, _, param = authorization_header.partition(" ")
        return scheme, param


security = CustomHTTPBearer()

# Algorithm for JWT token signing and verification
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
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
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
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=expires_delta
        )
        to_encode.update({"exp": expire})

    # Create the JWT token
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
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
    from local_DB.models import User

    return db.query(User).filter(User.email == email).first()


async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency that extracts and validates the user from credentials.

    Args:
        credentials: The HTTP authorization credentials
        db: The database session

    Returns:
        The user object if authentication is successful

    Raises:
        HTTPException: If authentication fails
    """
    # Extract the token from the authorization header
    token = credentials.credentials

    # Validate the JWT token and extract user information
    user_data = get_user_from_token(token)

    # Get the user from the database to ensure they exist
    user = get_user_from_db(user_data["email"], db)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
