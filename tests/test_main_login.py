from helpers.auth import decode_jwt_token, SESSION_COOKIE_NAME
from local_DB.db_dependencies import get_db
from main import app


def test_login_endpoint(app_client, local_db):
    """Test that the /login endpoint returns a valid JWT token"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Test data
    login_data = {"email": "test@example.com", "password": "test_password"}

    # Make request to the login endpoint
    response = app_client.post("/api/login", json=login_data)

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response contains a token
    token = response.json()
    assert token is not None

    # Verify that the token is a valid JWT token
    decoded = decode_jwt_token(token)
    assert decoded["email"] == login_data["email"]


def test_ui_login_endpoint(app_client, local_db):
    """Test that the POST /ui/login endpoint sets a cookie and redirects"""
    # Override the get_db dependency to return our local_db
    app.dependency_overrides[get_db] = lambda: local_db

    # Test data
    email = "test@example.com"
    password = "test_password"

    # Make request to the UI login endpoint with form data
    response = app_client.post(
        "/ui/login",
        data={"email": email, "password": password},
        follow_redirects=False,  # Don't follow redirects
    )

    # Check that the response is a redirect
    assert response.status_code == 303
    assert response.headers["location"] == "/ui/"

    # Check that the response contains a session cookie
    assert SESSION_COOKIE_NAME in response.cookies

    # Verify that the cookie contains a valid JWT token
    cookie_token = response.cookies[SESSION_COOKIE_NAME]
    decoded = decode_jwt_token(cookie_token)
    assert decoded["email"] == email
