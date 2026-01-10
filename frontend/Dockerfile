FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source code
COPY frontend/ frontend/

WORKDIR /app/frontend

# Expose Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]