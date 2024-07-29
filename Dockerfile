FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

RUN pip install --no-cache-dir uvicorn

RUN which uvicorn

RUN chmod -R 755 /root/.local/bin
RUN useradd -m myuser
RUN chown -R myuser:myuser /root/.local
USER myuser

# CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
CMD ["/usr/local/bin/uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000", "--env-file", ".env"]



