FROM python:3.9-slim

# Prevent Python from writing .pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Instant logging
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Requirements installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models ./models
COPY main.py .

EXPOSE 8000

# Server start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]