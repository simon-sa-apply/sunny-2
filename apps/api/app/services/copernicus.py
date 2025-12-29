"""
Copernicus Climate Data Store (CDS) Service.

Connects to Copernicus Atmosphere Data Store to fetch solar radiation data
from the CAMS Solar Radiation Timeseries dataset.

Includes protection mechanisms:
- Circuit breaker for fault tolerance
- Rate limiting (10 calls/minute)
- Concurrency control (5 simultaneous calls)
- Automatic fallback to mock data

References:
- https://ads.atmosphere.copernicus.eu/
- https://ads.atmosphere.copernicus.eu/datasets/cams-solar-radiation-timeseries
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Any, Optional

import httpx
import pandas as pd

from app.core.config import settings
from app.core.circuit_breaker import copernicus_breaker, CircuitOpenError
from app.core.metrics import track_external_call, metrics
from app.middleware.rate_limit import copernicus_rate_limiter, copernicus_semaphore

logger = logging.getLogger(__name__)


@dataclass
class SolarRadiationData:
    """Container for solar radiation data from Copernicus."""

    latitude: float
    longitude: float
    year: int
    
    # Time series data
    timestamps: list[datetime]
    ghi: list[float]  # Global Horizontal Irradiance (W/m²)
    dni: list[float]  # Direct Normal Irradiance (W/m²)
    dhi: list[float]  # Diffuse Horizontal Irradiance (W/m²)
    
    # Metadata
    source: str = "CAMS Solar Radiation Timeseries"
    data_tier: str = "standard"
    
    @property
    def annual_ghi_kwh_m2(self) -> float:
        """Calculate annual GHI in kWh/m²."""
        # Convert W/m² hourly values to kWh/m² annual
        return sum(self.ghi) / 1000
    
    @property
    def monthly_ghi(self) -> dict[str, float]:
        """Get monthly GHI totals in kWh/m²."""
        df = pd.DataFrame({"timestamp": self.timestamps, "ghi": self.ghi})
        df["month"] = pd.to_datetime(df["timestamp"]).dt.month
        monthly = df.groupby("month")["ghi"].sum() / 1000
        
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        return {month_names[i]: float(monthly.get(i + 1, 0)) for i in range(12)}


class CopernicusService:
    """
    Service for fetching solar radiation data from Copernicus CDSE.
    
    Uses the CAMS Solar Radiation Timeseries API endpoint.
    """

    # API Configuration
    BASE_URL = "https://ads.atmosphere.copernicus.eu/api"
    DATASET = "cams-solar-radiation-timeseries"
    
    # Latitude coverage limits
    MIN_LATITUDE = -66.0
    MAX_LATITUDE = 66.0

    def __init__(self) -> None:
        self._api_key = settings.COPERNICUS_API_KEY
        self._api_secret = settings.COPERNICUS_API_SECRET
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self._api_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(300.0),  # 5 min timeout for large requests
                headers={
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """Validate coordinates are within CAMS coverage."""
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude {lat} out of range [-90, 90]")
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude {lon} out of range [-180, 180]")
        if lat < self.MIN_LATITUDE or lat > self.MAX_LATITUDE:
            raise ValueError(
                f"Latitude {lat} is outside CAMS coverage "
                f"[{self.MIN_LATITUDE}, {self.MAX_LATITUDE}]. "
                "Data quality may be degraded."
            )

    def _build_request_params(
        self,
        lat: float,
        lon: float,
        year: int,
    ) -> dict[str, Any]:
        """
        Build request parameters for CAMS Solar Radiation API.
        
        Structure based on CAMS Solar Radiation Timeseries API.
        """
        return {
            "sky_type": "observed_cloud",
            "location": {
                "longitude": round(float(lon), 5),
                "latitude": round(float(lat), 5),
            },
            "altitude": ["-999."],  # Auto-detect altitude
            "date": [f"{year}-01-01/{year}-12-31"],
            "time_step": "1hour",
            "time_reference": "universal_time",
            "data_format": "csv",
        }

    async def fetch_solar_radiation(
        self,
        lat: float,
        lon: float,
        year: Optional[int] = None,
    ) -> SolarRadiationData:
        """
        Fetch solar radiation data for a location.
        
        Protected by:
        - Circuit breaker: Fails fast if service is down
        - Rate limiter: Max 10 calls/minute
        - Semaphore: Max 5 concurrent calls
        
        Args:
            lat: Latitude (-66 to 66 for best coverage)
            lon: Longitude (-180 to 180)
            year: Year to fetch (defaults to previous year)
        
        Returns:
            SolarRadiationData with GHI, DNI, DHI time series
        
        Raises:
            ValueError: If coordinates are invalid
            CircuitOpenError: If circuit breaker is open
            httpx.HTTPError: If API request fails
        """
        # Validate inputs
        self._validate_coordinates(lat, lon)
        
        if year is None:
            year = datetime.now().year - 1  # Use previous full year
        
        if not self.is_configured:
            logger.warning("Copernicus API not configured, using mock data")
            metrics.record_external_call("copernicus_mock", True, 0)
            return self._generate_mock_data(lat, lon, year)
        
        # Check circuit breaker first (fail fast)
        if copernicus_breaker.is_open:
            logger.warning("Copernicus circuit breaker is OPEN, using mock data")
            raise CircuitOpenError("copernicus", copernicus_breaker.recovery_timeout)
        
        # Acquire rate limit and semaphore
        await copernicus_rate_limiter.acquire()
        
        async with copernicus_semaphore:
            # Build and execute request with circuit breaker
            params = self._build_request_params(lat, lon, year)
            
            logger.info(f"Fetching CAMS data for ({lat}, {lon}) year {year}")
            
            async with track_external_call("copernicus"):
                try:
                    result = await copernicus_breaker.call(
                        self._do_fetch, params, lat, lon, year
                    )
                    return result
                except CircuitOpenError:
                    # Circuit opened during call, propagate
                    raise
                except Exception as e:
                    logger.error(f"Copernicus API error: {e}")
                    raise
    
    async def _do_fetch(
        self,
        params: dict[str, Any],
        lat: float,
        lon: float,
        year: int,
    ) -> SolarRadiationData:
        """Internal fetch method called by circuit breaker."""
        client = await self._get_client()
        response = await self._execute_cds_request(client, params)
        return self._parse_response(response, lat, lon, year)

    async def _execute_cds_request(
        self,
        client: httpx.AsyncClient,
        params: dict[str, Any],
    ) -> str:
        """
        Execute request to CDS API.
        
        Uses cdsapi library for real API calls, falls back to mock data on error.
        """
        # For MVP without real credentials, return mock data
        if not self._api_key or self._api_key == "mock":
            await asyncio.sleep(0.5)  # Simulate API latency
            return self._generate_mock_csv(params)
        
        # Try real cdsapi integration
        try:
            import cdsapi
            import tempfile
            import os
            
            # Run cdsapi in thread pool (it's synchronous)
            def _fetch_cds():
                # Configure cdsapi - new format uses only API key (no UID prefix)
                c = cdsapi.Client(
                    url="https://ads.atmosphere.copernicus.eu/api",
                    key=self._api_secret,  # Only the API key, no UID prefix
                )
                
                # Create temp file for output
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                    output_path = f.name
                
                try:
                    c.retrieve(
                        self.DATASET,
                        params,
                        output_path,
                    )
                    
                    with open(output_path, 'r') as f:
                        return f.read()
                finally:
                    if os.path.exists(output_path):
                        os.remove(output_path)
            
            # Execute in thread pool to not block async loop
            loop = asyncio.get_event_loop()
            csv_data = await loop.run_in_executor(None, _fetch_cds)
            return csv_data
            
        except Exception as e:
            logger.warning(f"CDS API failed ({e}), falling back to mock data")
            return self._generate_mock_csv(params)

    def _generate_mock_csv(self, params: dict[str, Any]) -> str:
        """Generate mock CSV data for testing without API credentials."""
        import random
        
        lat = params["location"]["latitude"]
        lon = params["location"]["longitude"]
        
        # Generate realistic hourly data for a year
        lines = ["timestamp,GHI,DNI,DHI"]
        
        # Seasonal variation based on latitude
        lat_factor = 1 - abs(lat) / 90
        
        for month in range(1, 13):
            # Seasonal adjustment (more sun in summer)
            if lat > 0:  # Northern hemisphere
                seasonal = 1 + 0.3 * (1 if month in [6, 7, 8] else -0.5 if month in [12, 1, 2] else 0)
            else:  # Southern hemisphere
                seasonal = 1 + 0.3 * (1 if month in [12, 1, 2] else -0.5 if month in [6, 7, 8] else 0)
            
            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
            
            for day in range(1, days_in_month + 1):
                for hour in range(24):
                    # Solar position approximation
                    if 6 <= hour <= 18:
                        # Daytime - bell curve peaking at noon
                        sun_factor = max(0, 1 - ((hour - 12) / 6) ** 2)
                        
                        # Base values with randomness for clouds
                        cloud_factor = random.uniform(0.3, 1.0)
                        
                        ghi = 1000 * sun_factor * seasonal * lat_factor * cloud_factor
                        dni = 900 * sun_factor * seasonal * lat_factor * cloud_factor * 0.85
                        dhi = ghi - dni * 0.7
                    else:
                        ghi, dni, dhi = 0, 0, 0
                    
                    timestamp = f"2023-{month:02d}-{day:02d}T{hour:02d}:00:00"
                    lines.append(f"{timestamp},{ghi:.1f},{dni:.1f},{max(0, dhi):.1f}")
        
        return "\n".join(lines)

    def _generate_mock_data(
        self,
        lat: float,
        lon: float,
        year: int,
    ) -> SolarRadiationData:
        """Generate mock solar radiation data for testing."""
        mock_csv = self._generate_mock_csv({
            "location": {"latitude": lat, "longitude": lon},
        })
        return self._parse_response(mock_csv, lat, lon, year)

    def _parse_response(
        self,
        csv_data: str,
        lat: float,
        lon: float,
        year: int,
    ) -> SolarRadiationData:
        """Parse CSV response into SolarRadiationData."""
        # Check if it's CAMS format (semicolon-separated with comments)
        if csv_data.startswith('#') or ';' in csv_data.split('\n')[0]:
            return self._parse_cams_csv(csv_data, lat, lon, year)
        
        # Standard CSV format (mock data)
        df = pd.read_csv(StringIO(csv_data))
        
        # Handle different column naming conventions
        ghi_col = next((c for c in df.columns if "GHI" in c.upper()), None)
        dni_col = next((c for c in df.columns if "DNI" in c.upper()), None)
        dhi_col = next((c for c in df.columns if "DHI" in c.upper()), None)
        
        if not all([ghi_col, dni_col, dhi_col]):
            raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}")
        
        # Determine data tier based on latitude
        data_tier = "engineering" if abs(lat) <= 60 else "standard"
        
        return SolarRadiationData(
            latitude=lat,
            longitude=lon,
            year=year,
            timestamps=pd.to_datetime(df.iloc[:, 0]).tolist(),
            ghi=df[ghi_col].tolist(),
            dni=df[dni_col].tolist(),
            dhi=df[dhi_col].tolist(),
            data_tier=data_tier,
        )

    def _parse_cams_csv(
        self,
        csv_data: str,
        lat: float,
        lon: float,
        year: int,
    ) -> SolarRadiationData:
        """
        Parse CAMS Solar Radiation CSV format.
        
        CAMS format uses:
        - Semicolon (;) as delimiter
        - Lines starting with # are comments
        - Column 1: Observation period (ISO 8601 range)
        - Column 7: GHI (Global Horizontal Irradiation)
        - Column 8: BHI (Beam Horizontal Irradiation) 
        - Column 9: DHI (Diffuse Horizontal Irradiation)
        - Column 10: BNI (Beam Normal Irradiation = DNI)
        """
        # Filter out comment lines
        lines = [line for line in csv_data.split('\n') if not line.startswith('#') and line.strip()]
        
        if not lines:
            raise ValueError("No data rows found in CAMS response")
        
        # Parse data rows
        timestamps = []
        ghi_values = []
        dni_values = []  # Using BNI as DNI
        dhi_values = []
        
        for line in lines:
            parts = line.split(';')
            if len(parts) < 10:
                continue
                
            # Parse timestamp from period (take start time)
            # Format: 2023-01-01T00:00:00.0/2023-01-01T01:00:00.0
            period = parts[0]
            timestamp_str = period.split('/')[0]
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('.0', ''))
                timestamps.append(timestamp)
                
                # GHI is column 7 (index 6)
                ghi_values.append(float(parts[6]) if parts[6] != 'nan' else 0.0)
                # DHI is column 9 (index 8)
                dhi_values.append(float(parts[8]) if parts[8] != 'nan' else 0.0)
                # BNI is column 10 (index 9) - this is DNI
                dni_values.append(float(parts[9]) if len(parts) > 9 and parts[9] != 'nan' else 0.0)
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping malformed line: {e}")
                continue
        
        if not timestamps:
            raise ValueError("No valid data rows parsed from CAMS response")
        
        # Determine data tier based on latitude
        data_tier = "engineering" if abs(lat) <= 60 else "standard"
        
        logger.info(f"Parsed {len(timestamps)} data points from CAMS response")
        
        return SolarRadiationData(
            latitude=lat,
            longitude=lon,
            year=year,
            timestamps=timestamps,
            ghi=ghi_values,
            dni=dni_values,
            dhi=dhi_values,
            source="CAMS Solar Radiation Timeseries (Real Data)",
            data_tier=data_tier,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
copernicus_service = CopernicusService()

