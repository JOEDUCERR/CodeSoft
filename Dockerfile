FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install docker CLI via docker.io (slim image limited); fallback to host docker via mounted socket. The python docker SDK uses socket directly.
RUN apt-get update && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

# For development, the CMD can be overridden; default to API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
