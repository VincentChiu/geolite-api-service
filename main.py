#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import geoip2.database
import geoip2.errors
from typing import Optional, Dict, Any
import uvicorn
from pydantic import BaseModel
import os
import ipaddress
import logging

# Configure logging - simplified output
logging.basicConfig(
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class GeoInfo(BaseModel):
    """Geographic location information model"""
    ip: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    asn: Optional[int] = None
    asn_organization: Optional[str] = None

class GeoIPService:
    """GeoIP query service class"""
    
    def __init__(self, city_db_path: str = None, 
                 country_db_path: str = None, 
                 asn_db_path: str = None):
        """Initialize service"""
        # Get current script directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set database file paths
        self.city_db_path = city_db_path or os.path.join(base_dir, "GeoLite2-City.mmdb")
        self.country_db_path = country_db_path or os.path.join(base_dir, "GeoLite2-Country.mmdb")
        self.asn_db_path = asn_db_path or os.path.join(base_dir, "GeoLite2-ASN.mmdb")
        
        # Validate database files exist
        self._validate_database_files()
        
        self.auth_token = os.environ.get("AUTH_TOKEN")
        
        # Create FastAPI application
        self.app = FastAPI(
            title="GeoIP Query Service", 
            description="Query geographic location information by IP address", 
            version="1.0.0"
        )
        
        # Authentication configuration
        self.security = HTTPBearer(auto_error=False)
        
        # Setup routes
        self._setup_routes()
    
    def _validate_database_files(self):
        """Validate database files exist"""
        required_files = [
            ("City Database", self.city_db_path),
            ("ASN Database", self.asn_db_path)
        ]
        
        for db_name, db_path in required_files:
            if not os.path.exists(db_path):
                logger.error(f"{db_name} file not found: {db_path}")
                raise FileNotFoundError(f"{db_name} file not found: {db_path}")
            else:
                logger.info(f"{db_name} file found: {db_path}")
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(None)):
        """Verify authentication token"""
        if self.auth_token is None:
            return True
        
        if credentials is None:
            logger.warning("Auth token required")
            raise HTTPException(
                status_code=401,
                detail="Authentication token required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.credentials != self.auth_token:
            logger.warning("Invalid auth token")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return True
    
    def get_client_ip(self, request: Request) -> str:
        """Get client real IP address"""
        # Check X-Forwarded-For header
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Take first IP
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            # Check X-Real-IP header
            x_real_ip = request.headers.get("X-Real-IP")
            if x_real_ip:
                ip = x_real_ip
            else:
                # Use direct connected client IP
                ip = request.client.host
        
        return ip
    
    def query_geo_info(self, ip_address: str, lang: str = "") -> Dict[str, Any]:
        """Query geographic location information for IP address"""
        geo_info = {
            "ip": ip_address,
            "country": None,
            "country_code": None,
            "region": None,
            "city": None,
            "latitude": None,
            "longitude": None,
            "timezone": None,
            "isp": None,
            "organization": None,
            "asn": None,
            "asn_organization": None
        }
        
        try:
            # Query city information
            with geoip2.database.Reader(self.city_db_path) as city_reader:
                try:
                    city_response = city_reader.city(ip_address)
                    
                    # Select language based on lang parameter
                    if lang:
                        geo_info["country"] = city_response.country.names.get(lang, city_response.country.name)
                        geo_info["region"] = city_response.subdivisions.most_specific.names.get(lang, city_response.subdivisions.most_specific.name)
                        geo_info["city"] = city_response.city.names.get(lang, city_response.city.name)
                    else:
                        # Default to English
                        geo_info["country"] = city_response.country.name
                        geo_info["region"] = city_response.subdivisions.most_specific.name
                        geo_info["city"] = city_response.city.name
                    
                    geo_info["country_code"] = city_response.country.iso_code
                    geo_info["latitude"] = float(city_response.location.latitude) if city_response.location.latitude else None
                    geo_info["longitude"] = float(city_response.location.longitude) if city_response.location.longitude else None
                    geo_info["timezone"] = city_response.location.time_zone
                except geoip2.errors.AddressNotFoundError:
                    pass  # No city data found, continue
                except Exception as e:
                    logger.error(f"City query error: {e}")
        except Exception as e:
            logger.error(f"City database error: {e}")
            raise HTTPException(status_code=500, detail=f"City database error: {str(e)}")
        
        try:
            # Query ASN information
            with geoip2.database.Reader(self.asn_db_path) as asn_reader:
                try:
                    asn_response = asn_reader.asn(ip_address)
                    geo_info["asn"] = int(asn_response.autonomous_system_number) if asn_response.autonomous_system_number else None
                    geo_info["asn_organization"] = asn_response.autonomous_system_organization
                    geo_info["isp"] = asn_response.autonomous_system_organization
                    geo_info["organization"] = asn_response.autonomous_system_organization
                except geoip2.errors.AddressNotFoundError:
                    pass  # No ASN data found, continue
                except Exception as e:
                    logger.error(f"ASN query error: {e}")
        except Exception as e:
            logger.error(f"ASN database error: {e}")
            raise HTTPException(status_code=500, detail=f"ASN database error: {str(e)}")
        
        return geo_info
    
    def _setup_routes(self):
        """Setup API routes"""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "geoip"}
       
        @self.app.get("/{ip_address}", response_model=GeoInfo)
        async def get_geo_info_by_ip(ip_address: str, request: Request, lang: str = "",
                                   credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Get geographic information for specified IP address"""
            # Verify token
            self.verify_token(credentials)

            # Validate IP address format
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid IP address format")

            return self.query_geo_info(ip_address, lang)
 
        @self.app.get("/", response_model=GeoInfo)
        async def get_geo_info_by_request_ip(request: Request, lang: str = "", 
                                           credentials: HTTPAuthorizationCredentials = Depends(self.security)):
            """Get geographic information for requester's IP"""
            # Verify token
            self.verify_token(credentials)
            client_ip = self.get_client_ip(request)
            return self.query_geo_info(client_ip, lang)
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            """HTTP exception handler"""
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail}
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            """General exception handler"""
            logger.error(f"Internal error: {str(exc)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Server internal error: {str(exc)}"}
            )
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run service"""
        logger.info(f"GeoIP service listening on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# Create global service instance
try:
    geoip_service = GeoIPService()
    logger.info("GeoIP service started")
except Exception as e:
    logger.error(f"Service init failed: {e}")
    raise

if __name__ == "__main__":
    geoip_service.run()
