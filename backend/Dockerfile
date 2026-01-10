FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for Pathway & compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/ backend/
COPY data/ data/

WORKDIR /app/backend

# Create a startup script to run both services
RUN echo '#!/bin/bash\n\
uvicorn api:app --host 0.0.0.0 --port 8000 &\n\
python main.py\n\
wait' > start.sh && chmod +x start.sh

CMD ["./start.sh"]