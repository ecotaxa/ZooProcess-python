import datetime
import uuid
from typing import Dict, Optional

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.requests import Request

from config_rdr import config
from helpers.logger import logger
from local_DB.db_dependencies import get_db
from local_DB.models import User, BlacklistedToken
from providers.ecotaxa_client import EcoTaxaApiClient


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
            # Check if authentication is in the cookie before raising an error
            if (
                SESSION_COOKIE_NAME in request.cookies
                and request.cookies[SESSION_COOKIE_NAME]
            ):
                # We have a cookie with a token, let the get_current_user_from_credentials function handle it
                return None
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        if scheme.lower() != "bearer":
            # Check if authentication is in the cookie before raising an error
            if (
                SESSION_COOKIE_NAME in request.cookies
                and request.cookies[SESSION_COOKIE_NAME]
            ):
                # We have a cookie with a token, let the get_current_user_from_credentials function handle it
                return None
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)

    @staticmethod
    def get_authorization_scheme_param(authorization_header: Optional[str]):
        if not authorization_header:
            return "", ""
        scheme, _, param = authorization_header.partition(" ")
        return scheme, param


security = CustomHTTPBearer()

# Algorithm for JWT token signing and verification
ALGORITHM = "HS256"

# Cookie name for session token
SESSION_COOKIE_NAME = "zoopp_session"


def decode_jwt_token(token: str, db: Optional[Session] = None) -> Dict[str, str]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode and validate
        db: Optional database session for checking token blacklist

    Returns:
        The decoded token payload if valid

    Raises:
        HTTPException: If the token is invalid, expired, or blacklisted
    """
    # Check if token is blacklisted
    if db is not None:
        blacklisted = (
            db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
        )
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )

    try:
        # Decode the JWT token
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        assert isinstance(payload, dict)
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

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=expires_delta
        )
        to_encode.update({"exp": expire})

    # Create the JWT token
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_from_token(token: str, db: Optional[Session] = None) -> str:
    """
    Extract user information from a JWT token.

    Args:
        token: The JWT token
        db: Optional database session for checking token blacklist

    Returns:
        User email extracted from the token
    """
    payload = decode_jwt_token(token, db)
    return payload.get("email", "")


def get_ecotaxa_token_from_token(token: str, db: Optional[Session] = None) -> str:
    """
    Extract EcoTaxa token in our token

    Args:
        token: The JWT token
        db: Optional database session for checking token blacklist

    Returns:
        EcoTaxa token.
    """
    payload = decode_jwt_token(token, db)
    return payload["token"]


def get_user_from_db(email: str, db) -> User:
    """
    Get a user from the database by email.

    Args:
        email: The user's email
        db: The database session

    Returns:
        The user if found, None otherwise
    """

    return db.query(User).filter(User.email == email).first()  # type:ignore


def user_from_db(name: str, email: str, db) -> User:
    """
    Ensure a user with the given email exists; create it if missing, and return its id.
    Lookup is performed by email.

    Args:
        name: The user's name (EcoTaxa conventions)
        email: The user's email address used for lookup and creation.
        db: The database session.

    Returns:
        str: The user's id (existing or newly created).
    """
    # Try to find existing user by email
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user  # type:ignore

    # Create a minimal user record if not found
    new_user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password="",  # No password stored here (auth handled externally)
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user  # type:ignore
    except IntegrityError:
        # In case of a race condition where the user was created concurrently
        db.rollback()
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user.id  # type:ignore
        raise


def blacklist_token(token: str, db: Session):
    """
    Add a token to the blacklist.

    Args:
        token: The JWT token to blacklist
        db: The database session

    Returns:
        The blacklisted token object
    """
    # Decode the token to get its expiration time
    try:
        payload = jwt.decode(
            token,
            config.SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": True},
        )
        if "exp" in payload:
            # Convert exp timestamp to datetime
            expires_at = datetime.datetime.fromtimestamp(
                payload["exp"], tz=datetime.timezone.utc
            )
        else:
            # If no expiration in token, set a default (e.g., 30 days from now)
            expires_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=30)
    except (jwt.PyJWTError, Exception):
        # If token is invalid or can't be decoded, set a default expiration
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=30
        )

    # Create a new blacklisted token entry
    blacklisted_token = BlacklistedToken(token=token, expires_at=expires_at)

    # Add to database
    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)

    # Clean up expired tokens
    cleanup_expired_tokens(db)

    return blacklisted_token


def cleanup_expired_tokens(db: Session):
    """
    Remove expired tokens from the blacklist to keep the table size manageable.

    Args:
        db: The database session
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    db.query(BlacklistedToken).filter(BlacklistedToken.expires_at < now).delete()
    db.commit()


def authenticate_user(email: str, password: str, db) -> str:
    """
    Authenticate a user with email and password.

    Args:
        email: The user's email
        password: The user's password
        db: The database session

    Returns:
        A dictionary containing the JWT token

    Raises:
        HTTPException: If authentication fails
    """
    # Validate the credentials against EcoTaxa server
    client = EcoTaxaApiClient(logger, config.ECOTAXA_SERVER, email, password)
    client.token = client.login()
    if client.token is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        who = client.whoami()

    user = user_from_db(who.name, who.email, db)

    # Create user data for the token
    user_data = {
        "sub": user.id,
        "name": user.name,
        "email": user.email,
        "token": client.token,
    }

    # Create a JWT token with 30-day expiration
    token = create_jwt_token(user_data, expires_delta=30 * 24 * 60 * 60)

    return token


async def get_current_user_from_credentials(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency that extracts and validates the user from credentials.

    Args:
        request: The request object to access cookies
        credentials: The HTTP authorization credentials
        db: The database session

    Returns:
        The user object if authentication is successful

    Raises:
        HTTPException: If authentication fails
    """
    token = await get_token_from_credentials(request, credentials)

    # Validate the JWT token and extract user information
    user_mail = get_user_from_token(token, db)

    # Get the user from the database to ensure they exist
    user = get_user_from_db(user_mail, db)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_ecotaxa_token_from_credentials(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> str:
    """
    FastAPI dependency that extracts EcoTaxa token from request.

    Args:
        request: The request object to access cookies
        credentials: The HTTP authorization credentials
        db: The database session

    Returns:
        The EcoTaxa token.

    Raises:
        HTTPException: If authentication problem
    """
    token = await get_token_from_credentials(request, credentials)

    return get_ecotaxa_token_from_token(token, db)


async def get_token_from_credentials(
    request: Request, credentials: HTTPAuthorizationCredentials
) -> str:
    token = None

    # Try to extract token from the authorization header
    if credentials:
        token = credentials.credentials

    # If no token from header, try to get it from the session cookie
    if not token and request:
        token = request.cookies.get(SESSION_COOKIE_NAME)

    # If still no token, authentication fails
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
