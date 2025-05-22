
# API Pipeline

A REST API to pilot the Ecotaxa pipelines


# requirement
```
pip install fastapi
pip install pydantic
pip install "uvicorn[standard]"
<!-- pip3 install opencv-python -->
pip install opencv-python
pip install requests
pip install numpy
```


# run it to dev

```
uvicorn main:app --reload
```

# Development Setup

For detailed installation instructions, please refer to the [Installation Guide](docs/installation.md).

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

# Environment Variables

The application uses the following environment variables:

- `APP_ENV`: Determines which configuration to use (`development` or `production`). Defaults to `development`.
- `WORKING_DIR`: The working directory where the application will look for configuration files and other resources. Defaults to the current working directory.

You can set these environment variables before running the application:

```bash
# Set the environment to production
export APP_ENV=production

# Set the working directory
export WORKING_DIR=/path/to/your/working/directory

# Run the application
python -m uvicorn main:app --reload
```

Or you can set them when running the application:

```bash
APP_ENV=production WORKING_DIR=/path/to/your/working/directory python -m uvicorn main:app --reload
```



# online docs

http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc




# The gateway API need other containeurs

## run DEEP-OC-multi_plankton_separation container
```bash
ssh niko
cd ~/complex/DEEP-OC-multi_plankton_separation
```

### build the container
```bash
docker build -t deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation .
```


### run it to have interactive shell
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

### run it in detach mode
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

### change local port 8888 to 8889, because already use by another container,      which ????
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8889:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

# Test with Thunder Client (obsolette)
In VSCode Thumder plugin, use the collection named Happy Pipeline

## test happy pipeline
+ to see if server alive
test DEEP plankton separation - niko alive ? : to see if multi_plankton_separation is alive on Niko server


# Run the gateway API in Docker

Built it
```bash
docker build -t gateway_api .
```
Run it
```
docker run -p 8000:8000 -v /Users/sebastiengalvagno/piqv/plankton/:/app/data --name happy_pipeline gateway_api
```

when use Docker use .env.production  else .env.development

at this moment, I can't run in docker because the path are linked to other apps
then it can't find the file

a possibility, to use docker, is to make the very long local path in the container
and use .env.development





# use the Swagger UI
open http://localhost:5000/ui

## through the VPN (niko run)
make a tunnel before open on with local address, port do not pass throught the VPN
```bash
ssh  -f niko -L 5001:localhost:5000 -N
open http://localhost:5001/ui
```


# new container
```bash
cd complex
git clone https://github.com/ai4os-hub/zooprocess-multiple-separator.git
cd zooprocess-multiple-separator/
docker build -t zooprocess-multiple-separator:1 .
docker build --no-cache -t zooprocess-multiple-separator:lastest .

docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8888:8888  zooprocess-multiple-separator:1
```

no detach mode to see error
```
docker run -ti -p 5000:5000 -p 6006:6006 -p 8888:8888  zooprocess-multiple-separator:1
```





# to generate a py client based on openapi.json
```
openapigenerator generate -i http://localhost:5000/openapi.json -g python -o ./src
```

# run unit test


```bash
python3 -m venv test_venv
source test_venv/bin/activate
pip install --upgrade pip 
pip install -r requirements.txt

python3 -m unittest discover tests
```

or one test
```bash
python -m unittest tests/*.py 
```
add -v for verbose mode, and ahave list of test functions

Run only on test function
```bash
python -m unittest tests.test_server.Test_server.test_dbserver_withconfig
```

# Database with SQLAlchemy

The application uses SQLAlchemy as an ORM (Object-Relational Mapping) to interact with the SQLite database. This provides a more Pythonic way to work with the database and makes it easier to maintain and extend the database schema.

## Database Models

Database models are defined in `src/db_models.py`. Each model represents a table in the database and inherits from the SQLAlchemy `Base` class.

Example model:
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Example(Base):
    __tablename__ = "example"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(String)
```

## Using SQLAlchemy in Your Code

There are two ways to interact with the database:

1. Using the backward-compatible `SQLiteDB` class (recommended for existing code):

```python
from src.local_db.sqlite_db import SQLiteDB

# Using the context manager
with SQLiteDB() as db:
  # Execute raw SQL queries
  cursor = db.execute("SELECT * FROM example")
  results = cursor.fetchall()
```

2. Using the new `SQLAlchemyDB` class (recommended for new code):

```python
from src.local_db.sqlite_db import SQLAlchemyDB
from src.local_db.models import Example

# Using the context manager
with SQLAlchemyDB() as db:
  # Create a new record
  example = Example(name="test", value="value")
  db.session.add(example)
  db.session.commit()

  # Query records
  results = db.session.query(Example).filter_by(name="test").all()
```

See the example script in `examples/sqlalchemy_example.py` for a complete example of using SQLAlchemy in the project.

# Command-Line Interface (CLI)

The application provides a command-line interface (CLI) for various administrative tasks. The CLI is built using Typer and provides a user-friendly interface with rich formatting.

## User Management CLI

The User Management CLI allows you to add, update, remove, and list users in the database.

### Installation

Make sure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

### Usage

```bash
# Show help
python -m commands.user_cli --help

# Add a new user
python -m commands.user_cli add --name "John Doe" --email "john@example.com"
# You will be prompted to enter and confirm a password

# Update an existing user
python -m commands.user_cli update --id "user_id" --name "New Name" --email "new@example.com"
# If you want to update the password, you will be prompted to enter and confirm it

# Remove a user
python -m commands.user_cli remove --id "user_id"
# You will be asked to confirm the removal unless you use the --force option

# List all users
python -m commands.user_cli list
```

### Commands

- `add`: Add a new user to the database
  - `--name`: User's full name (required)
  - `--email`: User's email address (required)
  - `--password`: User's password (will be prompted if not provided)
  - `--confirm-password`: Confirm password (will be prompted if not provided)

- `update`: Update an existing user in the database
  - `--id`: User ID (required)
  - `--name`: User's new name (optional)
  - `--email`: User's new email address (optional)
  - `--password`: User's new password (optional, will be prompted if provided)

- `remove`: Remove a user from the database
  - `--id`: User ID (required)
  - `--force` or `-f`: Force removal without confirmation (optional)

- `list`: List all users in the database
