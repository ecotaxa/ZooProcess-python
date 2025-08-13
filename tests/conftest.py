import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root and src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Add the ZooProcess-lib sibling src directory to the Python path
zooprocess_lib_path = Path(__file__).parent.parent.parent / "ZooProcess-lib" / "src"
if zooprocess_lib_path.exists():
    sys.path.append(str(zooprocess_lib_path))

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("WORKING_DIR", "tests")

from local_DB.models import Base, User
from main import app

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def project_python_path():
    """
    Return a list of Python paths for the project.

    This fixture provides a list of paths that should be added to sys.path for tests.
    It includes the project's src directory and may include other related directories
    such as the ZooProcess-lib sibling src directory.

    Example usage:
    ```python
    def test_something(project_python_path):
        # Use project_python_path as a list of paths to add to sys.path
        for path in project_python_path:
            sys.path.append(path)
    ```

    Returns:
        list: A list of paths to add to the Python path.
    """
    paths = [str(Path(__file__).parent.parent / "src")]

    if zooprocess_lib_path.exists():
        paths.append(str(zooprocess_lib_path))

    return paths


@pytest.fixture
def app_client():
    """
    Create a TestClient for the FastAPI app.

    This fixture creates a TestClient instance for testing API endpoints.

    Example usage:
    ```python
    def test_something(app_client):
        response = app_client.get("/some-endpoint")
        assert response.status_code == 200
    ```

    Returns:
        A FastAPI TestClient instance.
    """
    # Create the test client
    client = TestClient(app)

    # Return the client for use in tests
    yield client

    # Cleanup (equivalent to tearDown)
    app.dependency_overrides.clear()


@pytest.fixture
def server_client():
    """
    Launch a server in a subprocess and return a client to make requests to it.

    This fixture starts a server using uvicorn in a subprocess, waits for it to be ready,
    and then provides a way to make HTTP requests to it. It ensures the server is properly
    shut down after the test.

    Example usage:
    ```python
    def test_something(server_client):
        response = server_client.get("/some-endpoint")
        assert response.status_code == 200
    ```

    Returns:
        A requests.Session instance configured to make requests to the server.
    """
    # host and port of temp server
    host = "127.0.0.1"
    port = "8789"

    # Create temporary files for stdout and stderr
    stdout_file = tempfile.NamedTemporaryFile(
        prefix="server_stdout_", suffix=".log", delete=False
    )
    stderr_file = tempfile.NamedTemporaryFile(
        prefix="server_stderr_", suffix=".log", delete=False
    )

    # Create a temporary directory for DRIVES
    temp_drives_dir = tempfile.mkdtemp(prefix="zooprocess_drives_")

    # Set up environment with DRIVES
    env = os.environ.copy()
    env["DRIVES"] = temp_drives_dir

    # Add ZooProcess-lib to PYTHONPATH
    if Path(zooprocess_lib_path).exists():
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{zooprocess_lib_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = zooprocess_lib_path

    # Get the path to the src directory
    src_dir = Path(__file__).parent.parent / "src"

    # Start the server in a subprocess
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            host,
            "--port",
            port,
            "--app-dir",
            str(src_dir),
        ],
        stdout=stdout_file,
        stderr=stderr_file,
        env=env,
    )

    # Store file paths and temp directory for potential debugging and cleanup
    server_process.stdout_path = stdout_file.name
    server_process.stderr_path = stderr_file.name
    server_process.temp_drives_dir = temp_drives_dir

    # Close file handles (subprocess will keep writing to the files)
    stdout_file.close()
    stderr_file.close()

    # Create a session for making requests
    session = requests.Session()
    base_url = f"http://{host}:{port}"

    # Wait for the server to start
    max_retries = 10
    server_started = False
    for i in range(max_retries):
        try:
            # Try to connect to the server
            response = session.get(f"{base_url}/ping", timeout=0.5)
            if 200 <= response.status_code < 300:
                server_started = True
                break
        except requests.exceptions.ConnectionError:
            # Server not ready yet, wait and retry
            time.sleep(0.5)

    if not server_started:
        # Server failed to start
        server_process.terminate()
        server_process.wait()

        # Read the content of the log files
        stdout_content = ""
        stderr_content = ""
        try:
            with open(server_process.stdout_path, "r") as f:
                stdout_content = f.read()
            with open(server_process.stderr_path, "r") as f:
                stderr_content = f.read()
        except Exception as e:
            print(f"Error reading log files: {e}")

        # Clean up the log files
        try:
            os.unlink(server_process.stdout_path)
            os.unlink(server_process.stderr_path)
        except Exception as e:
            print(f"Error removing log files: {e}")

        # Clean up the temporary DRIVES directory
        try:
            os.rmdir(server_process.temp_drives_dir)
        except Exception as e:
            print(f"Error removing temporary DRIVES directory: {e}")

        # Raise an exception with the log content
        raise Exception(
            f"Server failed to start.\nSTDOUT:\n{stdout_content}\nSTDERR:\n{stderr_content}"
        )

    # Add a method to the session to make it behave like TestClient
    def get_url(url):
        if url.startswith("/"):
            url = f"{base_url}{url}"
        return url

    original_get = session.get
    original_post = session.post
    original_put = session.put
    original_delete = session.delete

    session.get = lambda url, **kwargs: original_get(get_url(url), **kwargs)
    session.post = lambda url, **kwargs: original_post(get_url(url), **kwargs)
    session.put = lambda url, **kwargs: original_put(get_url(url), **kwargs)
    session.delete = lambda url, **kwargs: original_delete(get_url(url), **kwargs)

    # Return the session for use in tests
    yield session

    # Cleanup: terminate the server process
    server_process.terminate()
    server_process.wait()

    # Clean up the log files
    try:
        os.unlink(server_process.stdout_path)
        os.unlink(server_process.stderr_path)
    except Exception as e:
        print(f"Error removing log files during cleanup: {e}")

    # Clean up the temporary DRIVES directory
    try:
        os.rmdir(server_process.temp_drives_dir)
    except Exception as e:
        print(f"Error removing temporary DRIVES directory: {e}")


@pytest.fixture
def local_db():
    """
    Create a SQLite database in a file for testing.

    This fixture creates a database, initializes the schema,
    and adds a user with known credentials for testing.

    The test user has the following credentials:
        - email: "test@example.com"
        - password: "test_password"
        - name: "Test User"

    Example usage:
    ```python
    def test_something(local_db):
        # Query the user from the database
        user = local_db.query(User).filter(User.email == "test@example.com").first()

        # Use the user for authentication
        from auth import get_user_from_db
        user = get_user_from_db("test@example.com", local_db)
    ```

    Returns:
        A SQLAlchemy session connected to the file-based database.
    """
    # Create a temporary file-based SQLite database
    temp_db_file = f"test_db_{uuid.uuid4()}.db"
    engine = create_engine(f"sqlite:///{temp_db_file}")

    # Create all tables in the database
    Base.metadata.create_all(engine)

    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create a test user
    test_user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        password="test_password",
    )

    # Add the user to the database
    session.add(test_user)
    session.commit()

    # Return the session for use in tests
    yield session

    # Clean up after the test
    try:
        session.close()
    except Exception as e:
        # Ignore errors when closing the session
        # This prevents issues during teardown
        pass

    # Remove the temporary database file
    try:
        if os.path.exists(temp_db_file):
            os.remove(temp_db_file)
    except Exception as e:
        # Ignore errors when removing the file
        pass
