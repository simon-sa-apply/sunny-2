"""
PVGIS (Photovoltaic Geographical Information System) Service.

Provides global solar radiation data from the European Commission's
Joint Research Centre. Covers regions outside CAMS coverage including
Chile, Americas, and other global locations.

Includes protection mechanisms:
- Circuit breaker for fault tolerance
- Rate limiting (20 calls/minute)
- Concurrency control (10 simultaneous calls)
- Automatic database fallback selection

References:
- https://re.jrc.ec.europa.eu/pvg_tools/en/
- https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.core.circuit_breaker import CircuitOpenError, pvgis_breaker
from app.core.metrics import track_external_call
from app.middleware.rate_limit import pvgis_rate_limiter, pvgis_semaphore

logger = logging.getLogger(__name__)


@dataclass
class PVGISRadiationData:
    """Container for solar radiation data from PVGIS."""

    latitude: float
    longitude: float
    year: int

    # Monthly averages (kWh/m²/day)
    monthly_ghi: dict[str, float]
    monthly_dni: dict[str, float]
    monthly_dhi: dict[str, float]

    # Annual totals (kWh/m²)
    annual_ghi: float
    annual_dni: float
    annual_dhi: float

    # Optimal angles
    optimal_tilt: float
    optimal_azimuth: float

    # Metadata
    elevation: float
    source: str = "PVGIS-SARAH2"
    data_tier: str = "standard"

    @property
    def annual_ghi_kwh_m2(self) -> float:
        """Annual GHI in kWh/m²."""
        return self.annual_ghi


class PVGISService:
    """
    Service for fetching solar radiation data from PVGIS.

    PVGIS provides global coverage and is used as fallback
    when CAMS data is not available.
    """

    BASE_URL = "https://re.jrc.ec.europa.eu/api/v5_2"

    # PVGIS database coverage
    DATABASES = {
        "PVGIS-SARAH2": {
            "coverage": "Europe, Africa, Middle East, Asia",
            "years": "2005-2020",
        },
        "PVGIS-NSRDB": {
            "coverage": "Americas",
            "years": "1998-2019",
        },
        "PVGIS-ERA5": {
            "coverage": "Global",
            "years": "2005-2020",
        },
    }

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,      # Connection timeout
                    read=25.0,        # Read timeout (reduced from 60s)
                    write=10.0,       # Write timeout
                    pool=5.0,         # Pool timeout
                ),
                headers={"Accept": "application/json"},
            )
        return self._client

    def _select_database(self, lat: float, lon: float) -> str:
        """
        Select the best PVGIS database for the location.

        - Americas: PVGIS-NSRDB (best quality for this region)
        - Europe/Africa/Middle East: PVGIS-SARAH2
        - Global fallback: PVGIS-ERA5
        """
        # Americas (Western Hemisphere)
        if -170 < lon < -30:
            return "PVGIS-NSRDB"

        # Europe, Africa, Middle East, Western Asia
        if -30 < lon < 60 and -35 < lat < 70:
            return "PVGIS-SARAH2"

        # Global fallback
        return "PVGIS-ERA5"

    async def fetch_solar_radiation(
        self,
        lat: float,
        lon: float,
        year: int | None = None,
    ) -> PVGISRadiationData:
        """
        Fetch solar radiation data from PVGIS.

        Protected by:
        - Circuit breaker: Fails fast if service is down
        - Rate limiter: Max 20 calls/minute
        - Semaphore: Max 10 concurrent calls

        Uses the PVcalc endpoint which provides monthly irradiation data
        for any location worldwide (using ERA5 for global coverage).

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            year: Not used (PVGIS returns TMY - Typical Meteorological Year)

        Returns:
            PVGISRadiationData with monthly and annual radiation values

        Raises:
            CircuitOpenError: If circuit breaker is open
            httpx.HTTPError: If API request fails
        """
        if year is None:
            year = datetime.now().year - 1

        # Check circuit breaker first (fail fast)
        if pvgis_breaker.is_open:
            logger.warning("PVGIS circuit breaker is OPEN")
            raise CircuitOpenError("pvgis", pvgis_breaker.recovery_timeout)

        database = self._select_database(lat, lon)

        # Acquire rate limit and semaphore
        await pvgis_rate_limiter.acquire()

        async with pvgis_semaphore:
            logger.info(f"Fetching PVGIS data for ({lat}, {lon}) using {database}")

            async with track_external_call("pvgis"):
                try:
                    result = await pvgis_breaker.call(
                        self._do_fetch, lat, lon, year, database
                    )
                    return result
                except CircuitOpenError:
                    raise
                except Exception as e:
                    logger.error(f"PVGIS API error: {e}")
                    raise

    async def _do_fetch(
        self,
        lat: float,
        lon: float,
        year: int,
        database: str,
    ) -> PVGISRadiationData:
        """Internal fetch method called by circuit breaker."""
        client = await self._get_client()

        # Use PVcalc endpoint - more reliable and comprehensive
        params = {
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "peakpower": 1,  # 1 kWp reference system
            "loss": 14,     # Standard system losses
            "outputformat": "json",
            "raddatabase": database,
        }

        response = await client.get(
            f"{self.BASE_URL}/PVcalc",
            params=params,
        )

        if response.status_code != 200:
            logger.warning(f"PVGIS {database} returned {response.status_code}, trying ERA5")
            # Try global ERA5 database as fallback
            params["raddatabase"] = "PVGIS-ERA5"
            database = "PVGIS-ERA5"
            response = await client.get(
                f"{self.BASE_URL}/PVcalc",
                params=params,
            )

        response.raise_for_status()
        data = response.json()

        return self._parse_response(data, lat, lon, year, database)

    def _parse_response(
        self,
        data: dict[str, Any],
        lat: float,
        lon: float,
        year: int,
        database: str,
    ) -> PVGISRadiationData:
        """Parse PVGIS PVcalc JSON response."""

        inputs = data.get("inputs", {})
        outputs = data.get("outputs", {})

        # Get location metadata
        location = inputs.get("location", {})
        elevation = location.get("elevation", 0)

        # Get actual database used
        meteo = inputs.get("meteo_data", {})
        actual_db = meteo.get("radiation_db", database)

        # Parse monthly data from PVcalc format
        # outputs.monthly.fixed contains array of monthly data
        monthly_fixed = outputs.get("monthly", {}).get("fixed", [])

        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        monthly_ghi = {}
        monthly_dni = {}
        monthly_dhi = {}

        annual_ghi = 0
        annual_dni = 0
        annual_dhi = 0

        for month_data in monthly_fixed:
            month_idx = month_data.get("month", 1) - 1
            if 0 <= month_idx < 12:
                month_name = month_names[month_idx]

                # PVcalc returns:
                # H(i)_m = Global irradiation on inclined plane (kWh/m²/month)
                # For horizontal plane (slope=0), this equals GHI
                ghi = month_data.get("H(i)_m", 0)

                # Estimate DNI and DHI from GHI (typical split)
                # DNI ≈ 70% of GHI, DHI ≈ 30% of GHI (approximate)
                dni = ghi * 0.70
                dhi = ghi * 0.30

                monthly_ghi[month_name] = ghi
                monthly_dni[month_name] = dni
                monthly_dhi[month_name] = dhi

                annual_ghi += ghi
                annual_dni += dni
                annual_dhi += dhi

        # Get optimal angles from mounting system if available
        mounting = inputs.get("mounting_system", {}).get("fixed", {})
        slope_info = mounting.get("slope", {})
        azimuth_info = mounting.get("azimuth", {})

        # Default optimal values based on latitude
        optimal_tilt = slope_info.get("value", abs(lat))
        optimal_azimuth = azimuth_info.get("value", 0 if lat < 0 else 180)  # North for S.hemisphere

        # Determine data tier based on database
        data_tier = "engineering" if actual_db in ["PVGIS-SARAH2", "PVGIS-NSRDB"] else "standard"

        logger.info(f"PVGIS parsed: {len(monthly_ghi)} months, {annual_ghi:.1f} kWh/m²/year")

        return PVGISRadiationData(
            latitude=lat,
            longitude=lon,
            year=year,
            monthly_ghi=monthly_ghi,
            monthly_dni=monthly_dni,
            monthly_dhi=monthly_dhi,
            annual_ghi=annual_ghi,
            annual_dni=annual_dni,
            annual_dhi=annual_dhi,
            optimal_tilt=optimal_tilt,
            optimal_azimuth=optimal_azimuth,
            elevation=elevation,
            source=f"PVGIS ({actual_db})",
            data_tier=data_tier,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
pvgis_service = PVGISService()

