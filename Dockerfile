FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

# Single worker keeps APScheduler from starting duplicate poll jobs.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
