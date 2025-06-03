from typing import Optional

from Models import User
from modern.ids import hash_from_user_name

# Hardcoded list of users
USERS = [
    {"id": "user1", "name": "n/a", "email": "user@example.com"},
]


def get_mock_user() -> User:
    """
    Returns a mock user.

    Returns:
        User: A mock user object.
    """
    return User(**USERS[0])


def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Returns a user by its ID.

    Args:
        user_id (str): The ID of the user to retrieve.

    Returns:
        User: The user with the specified ID, or None if not found.
    """
    for user_data in USERS:
        if user_data["id"] == user_id:
            return User(**user_data)
    return None


def user_with_name(user_name: str) -> User:
    return User(
        id=hash_from_user_name(user_name), name=user_name, email="unknown@unknown.com"
    )
