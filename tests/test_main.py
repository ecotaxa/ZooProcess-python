import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from fastapi.testclient import TestClient

from main import app, get_db
from src.Models import User, LoginReq
from src.importe import getInstrumentFromSN
from src.auth import decode_jwt_token, get_user_from_db
from src.db_models import User as DBUser


class Test_main(unittest.TestCase):

    def setUp(self):
        # Create a mock database session
        self.mock_db = MagicMock()

        # Create a mock user for testing
        self.mock_user = MagicMock(spec=DBUser)
        self.mock_user.id = "123456789"
        self.mock_user.name = "John Doe"
        self.mock_user.email = "test@example.com"
        self.mock_user.password = "test_password"

        # Override the get_db dependency to return our mock session
        app.dependency_overrides[get_db] = lambda: self.mock_db

        # Create the test client
        self.client = TestClient(app)

    def tearDown(self):
        # Remove the dependency override after each test
        app.dependency_overrides.clear()

    @patch("src.auth.get_user_from_db")
    def test_login_endpoint(self, mock_get_user_from_db):
        """Test that the /login endpoint returns a valid JWT token"""
        # Set up the mock to return our mock user
        mock_get_user_from_db.return_value = self.mock_user

        # Test data
        login_data = {"email": "test@example.com", "password": "test_password"}

        # Make request to the login endpoint
        response = self.client.post("/login", json=login_data)

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that the response contains a token
        token = response.json()
        self.assertIsNotNone(token)

        # Verify that the token is a valid JWT token
        decoded = decode_jwt_token(token)
        self.assertEqual(decoded["email"], login_data["email"])

        # Verify that get_user_from_db was called with the correct arguments
        mock_get_user_from_db.assert_called_once_with(login_data["email"], self.mock_db)

    @patch("src.auth.get_user_from_db")
    def test_users_me_endpoint_with_valid_token(self, mock_get_user_from_db):
        """Test that the /users/me endpoint returns user information with a valid token"""
        # Set up the mock to return our mock user
        mock_get_user_from_db.return_value = self.mock_user

        # First, get a valid token by logging in
        login_data = {"email": "test@example.com", "password": "test_password"}
        with patch("src.auth.get_user_from_db", return_value=self.mock_user):
            login_response = self.client.post("/login", json=login_data)
            token = login_response.json()

        # Make request to the /users/me endpoint with the token
        response = self.client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        # Check that the response is successful
        self.assertEqual(response.status_code, 200)

        # Check that the response contains user information
        user_data = response.json()
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["email"], login_data["email"])

        # Verify that get_user_from_db was called with the correct arguments
        mock_get_user_from_db.assert_called_with(login_data["email"], self.mock_db)

    def test_users_me_endpoint_without_token(self):
        """Test that the /users/me endpoint returns 401 without a token"""
        # Make request to the /users/me endpoint without a token
        response = self.client.get("/users/me")

        # Check that the response is 401 Unauthorized
        self.assertEqual(response.status_code, 401)

    def test_users_me_endpoint_with_invalid_token(self):
        """Test that the /users/me endpoint returns 401 with an invalid token"""
        # Make request to the /users/me endpoint with an invalid token
        response = self.client.get(
            "/users/me", headers={"Authorization": "Bearer invalid_token"}
        )

        # Check that the response is 401 Unauthorized
        self.assertEqual(response.status_code, 401)
