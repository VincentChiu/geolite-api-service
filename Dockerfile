# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download GeoLite2 Database
RUN wget -O GeoLite2-ASN.mmdb      https://git.io/GeoLite2-ASN.mmdb
RUN wget -O GeoLite2-City.mmdb     https://git.io/GeoLite2-City.mmdb
RUN wget -O GeoLite2-Country.mmdb  https://git.io/GeoLite2-Country.mmdb

# Copy application files
COPY main.py .

# Create non-root user for security
RUN useradd -m -u 1000 geoip && chown -R geoip:geoip /app
USER geoip

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Run the application
CMD ["python", "main.py"]
