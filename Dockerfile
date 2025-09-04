# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /healthsync

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    gfortran \
    libblas3 \
    liblapack3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY ./app ./app
COPY ./data ./data
COPY ./scripts ./scripts

# Set Python path
ENV PYTHONPATH=/healthsync

# Expose port for FastAPI
EXPOSE 8000

# Default command to run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
