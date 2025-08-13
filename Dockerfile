# OpenCV has no musl wheel, so alpine is tricky to have working
# bookworm is debian 12.5
FROM python:3.12.11-slim-bookworm

RUN pip install --upgrade pip

# Build information
LABEL org.opencontainers.image.created="2025-08-11"
LABEL org.opencontainers.image.authors="ZooProcess Team"
LABEL org.opencontainers.image.url="https://github.com/ecotaxa/ZooProcess-python"
LABEL org.opencontainers.image.documentation="https://github.com/ecotaxa/ZooProcess-python/docs"
LABEL org.opencontainers.image.source="https://github.com/ecotaxa/ZooProcess-python"
LABEL org.opencontainers.image.version="0.1b"
LABEL org.opencontainers.image.vendor="ZooProcess"
LABEL org.opencontainers.image.title="ZooProcess Python"
LABEL org.opencontainers.image.description="ZooProcess Python application for processing Zooscan plankton images"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src /app
# Fetch compiled front-end from GH
ADD https://github.com/ecotaxa/ZooProcess-front/releases/latest/download/dist.tgz client.tgz
RUN cd / && tar xvf app/client.tgz && rm app/client.tgz
COPY src/static /static

EXPOSE 80

ENV APP_ENV=prod
# TODO RUN python user_cli.py add --name admin --email admin@nowhere.com --password password --confirm-password password
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]