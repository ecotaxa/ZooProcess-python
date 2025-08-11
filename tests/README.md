# ZooProcess API Tests

This directory contains tests for the ZooProcess API. The tests are organized by module and functionality.

## Test Structure

- `test_auth.py`: Tests for JWT authentication functionality in `src/auth.py`
- `test_main.py`: Tests for API endpoints in `main.py`, including authentication endpoints
- Other test files test various components of the application

## Running Tests

### Prerequisites

Make sure you have installed all the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Tests

To run tests for a specific module:

```bash
pytest tests/test_auth.py
```

To run a specific test:

```bash
pytest tests/test_auth.py::Test_auth::test_create_jwt_token
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=src tests/
```

This will show you the test coverage for the `src` directory.

## Authentication Tests

The authentication tests verify:

1. JWT token creation and validation
2. User information extraction from tokens
3. Endpoint behavior with valid, invalid, and missing tokens

### Unit Tests (`test_auth.py`)

- `test_create_jwt_token`: Tests that JWT tokens are created correctly
- `test_decode_jwt_token_valid`: Tests that valid JWT tokens are decoded correctly
- `test_decode_jwt_token_expired`: Tests that expired JWT tokens are rejected
- `test_decode_jwt_token_invalid`: Tests that invalid JWT tokens are rejected
- `test_get_user_from_token`: Tests that user information is extracted correctly from tokens

### Integration Tests (`test_main.py`)

- `test_login_endpoint`: Tests that the `/login` endpoint returns a valid JWT token
- `test_users_me_endpoint_with_valid_token`: Tests that the `/users/me` endpoint returns user information with a valid token
- `test_users_me_endpoint_without_token`: Tests that the `/users/me` endpoint returns 401 without a token
- `test_users_me_endpoint_with_invalid_token`: Tests that the `/users/me` endpoint returns 401 with an invalid token