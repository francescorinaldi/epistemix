FROM python:3.11-slim

WORKDIR /app

# Install worker dependencies
COPY worker/requirements.txt ./worker/
RUN pip install --no-cache-dir -r worker/requirements.txt

# Copy the core library
COPY src/ ./src/
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[live]"

# Copy worker code
COPY worker/ ./worker/

CMD ["python", "worker/main.py"]
