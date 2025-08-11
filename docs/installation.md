# Installation Guide for ZooProcess-python

This guide provides detailed instructions for setting up and installing ZooProcess-python for development purposes.

## Prerequisites

Before installing ZooProcess-python, ensure you have the following prerequisites installed:

- Python 3.10 or higher
- pip (Python package installer)
- git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ecotaxa/ZooProcess-python.git
cd ZooProcess-python
```

### 2. Create a Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python projects:

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

On Linux/macOS:
```bash
source venv/bin/activate
```

On Windows:
```bash
venv\Scripts\activate
```

### 4. Install Dependencies from requirements.txt

Install all required dependencies using pip:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Note on uvicorn installation
If you encounter issues with uvicorn installation from requirements.txt, you can install it manually:

```bash
pip install uvicorn
```

### 5. Run the Application

After installing all dependencies, you can run the application using:

```bash
python -m uvicorn main:app --reload
```

## Environment Variables

The application uses the following environment variables:

- `APP_ENV`: Determines which configuration to use (`dev` or `prod`). Defaults to `dev`.
- `WORKING_DIR`: The working directory where the application will look for DB file and write logs. Defaults to the current working directory.

You can set these environment variables before running the application:

```bash
# Set the environment to production
export APP_ENV=prod

# Set the working directory
export WORKING_DIR=/path/to/your/working/directory

# Run the application
python -m uvicorn main:app --reload
```