# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libffi-dev \
    libxml2-dev \
    libxslt-dev \
    libssl-dev \
    python-dev \
    gcc \
    musl-dev \
    mupdf \
    mupdf-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Create directories
RUN mkdir -p uploads

# Set permissions
RUN chmod -R 755 /app

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
