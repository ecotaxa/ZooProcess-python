# Build stage
FROM python:3.9-slim as build

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Copy installed packages from build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the application from build stage
COPY --from=build /app /app

# Install Uvicorn
RUN pip install --no-cache-dir uvicorn
RUN pip install --upgrade pip
RUN pip list

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--env-file", ".env"]
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# CMD ["pip" , "list"]
CMD ["which", "uvicorn"]
