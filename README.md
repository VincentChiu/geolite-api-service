# GeoLite API Service

A RESTful API service for querying geographic location information using MaxMind's GeoLite2 databases. 

## API Endpoints

### 1. Get Geographic Information by IP Address
```
GET /{ip_address}?lang={language}
```

**Parameters:**
- `ip_address` (path): Target IP address to query
- `lang` (query, optional): Language code for localized names (e.g., 'en', 'jp', 'zh-CN')

**Response:**
```json
{
  "ip": "8.8.8.8",
  "country": "United States",
  "country_code": "US",
  "region": "California",
  "city": "Mountain View",
  "latitude": 37.4056,
  "longitude": -122.0775,
  "timezone": "America/Los_Angeles",
  "isp": "Google LLC",
  "organization": "Google LLC",
  "asn": 15169,
  "asn_organization": "Google LLC"
}
```

### 2. Get Geographic Information for Requester
```
GET /?lang={language}
```

Automatically detects the requester's IP address and returns geographic information.

**Parameters:**
- `lang` (query, optional): Language code for localized names

### 3. Health Check
```
GET /health
```

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "geoip"
}
```

## Quick Start

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.10+ with pip

### Option 1: Using Docker (Recommended)

1. **Build Docker Image**
```bash
docker buildx build --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -t geolite-api:latest .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d
```

### Option 2: Manual Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Download GeoLite2 Database Files**
```bash
# Download required database files
wget -O GeoLite2-ASN.mmdb      https://git.io/GeoLite2-ASN.mmdb
wget -O GeoLite2-City.mmdb     https://git.io/GeoLite2-City.mmdb
wget -O GeoLite2-Country.mmdb  https://git.io/GeoLite2-Country.mmdb
```

3. **Run the Service**
```bash
python main.py
```

## Configuration

### Environment Variables

- `AUTH_TOKEN` (optional): Bearer token for API authentication
- `PYTHONUNBUFFERED` (optional): Set to `1` for better logging in containers

### Database Files

The service requires the following MaxMind GeoLite2 database files:
- `GeoLite2-City.mmdb`: City-level geographic data
- `GeoLite2-ASN.mmdb`: ASN and ISP information
- `GeoLite2-Country.mmdb`: Country-level data (optional)

## Authentication

To enable authentication, set the `AUTH_TOKEN` environment variable:

```bash
export AUTH_TOKEN="your-secret-token"
```

Then include the token in your requests:
```bash
curl -H "Authorization: Bearer your-secret-token" http://localhost:8080/8.8.8.8
```

## Examples

### Basic Usage
```bash
# Query specific IP
curl http://localhost:8080/8.8.8.8

# Query with Chinese localization
curl http://localhost:8080/8.8.8.8?lang=zh-CN

# Query requester's own IP
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health
```

### With Authentication
```bash
curl -H "Authorization: Bearer your-token" http://localhost:8080/8.8.8.8
```

## Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **uvicorn**: ASGI server implementation
- **geoip2**: MaxMind GeoIP2 Python library
- **pydantic**: Data validation using Python type annotations
- **python-multipart**: Form data parsing support

## License

This project uses MaxMind's GeoLite2 databases, which are distributed under the [GeoLite2 End User License Agreement](https://www.maxmind.com/en/geolite2/eula).

