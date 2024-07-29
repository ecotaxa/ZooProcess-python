FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

RUN useradd -m myuser
USER myuser

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
