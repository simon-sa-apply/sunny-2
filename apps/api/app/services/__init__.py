"""Business logic services."""

from app.services.copernicus import CopernicusService, SolarRadiationData, copernicus_service
from app.services.interpolation import InterpolationModel, generate_interpolation_model
from app.services.pvgis import PVGISRadiationData, PVGISService, pvgis_service
from app.services.solar_calculator import SolarCalculator, SolarEstimate
from app.services.solar_data import SolarDataService, UnifiedSolarData, solar_data_service

__all__ = [
    # Copernicus (CAMS)
    "CopernicusService",
    "SolarRadiationData",
    "copernicus_service",
    # PVGIS
    "PVGISService",
    "PVGISRadiationData",
    "pvgis_service",
    # Unified Solar Data
    "SolarDataService",
    "UnifiedSolarData",
    "solar_data_service",
    # Calculator
    "SolarCalculator",
    "SolarEstimate",
    # Interpolation
    "InterpolationModel",
    "generate_interpolation_model",
]

