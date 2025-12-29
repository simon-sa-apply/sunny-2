"""Base plugin interface for country-specific solar regulations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CountryConstants:
    """Country-specific constants and regulatory factors."""

    # Country identification
    country_code: str
    country_name: str
    
    # Data quality tier
    data_tier: str  # 'engineering' | 'standard'
    
    # Grid and billing factors
    net_billing_factor: float  # Factor for grid injection value (0-1)
    grid_efficiency: float  # Grid transmission efficiency
    
    # Environmental impact
    co2_factor_kg_per_kwh: float  # CO2 avoided per kWh generated
    
    # Regulatory reference
    regulatory_reference: str
    
    # Currency for economic calculations
    currency: str
    currency_symbol: str
    
    # Average electricity price (for savings calculations)
    avg_electricity_price: float  # per kWh
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "country_code": self.country_code,
            "country_name": self.country_name,
            "data_tier": self.data_tier,
            "factors": {
                "net_billing": self.net_billing_factor,
                "grid_efficiency": self.grid_efficiency,
                "co2_factor_kg_per_kwh": self.co2_factor_kg_per_kwh,
            },
            "regulatory_reference": self.regulatory_reference,
            "economics": {
                "currency": self.currency,
                "currency_symbol": self.currency_symbol,
                "avg_electricity_price": self.avg_electricity_price,
            },
        }


class CountryPlugin(ABC):
    """Base class for country-specific plugins."""

    @property
    @abstractmethod
    def constants(self) -> CountryConstants:
        """Return country constants."""
        ...

    def apply_net_billing(self, generation_kwh: float) -> float:
        """Apply net billing factor to generation."""
        return generation_kwh * self.constants.net_billing_factor

    def calculate_grid_output(self, generation_kwh: float) -> float:
        """Calculate actual grid output after transmission losses."""
        return generation_kwh * self.constants.grid_efficiency

    def calculate_co2_savings(self, generation_kwh: float) -> float:
        """Calculate CO2 savings in kg."""
        return generation_kwh * self.constants.co2_factor_kg_per_kwh

    def calculate_savings(
        self,
        generation_kwh: float,
        custom_price: Optional[float] = None,
    ) -> dict[str, Any]:
        """Calculate economic savings."""
        price = custom_price or self.constants.avg_electricity_price
        grid_output = self.calculate_grid_output(generation_kwh)
        net_billing = self.apply_net_billing(grid_output)
        
        annual_savings = net_billing * price
        monthly_avg = annual_savings / 12
        
        return {
            "annual_savings": round(annual_savings, 2),
            "monthly_average": round(monthly_avg, 2),
            "currency": self.constants.currency,
            "currency_symbol": self.constants.currency_symbol,
            "price_per_kwh": price,
            "co2_savings_kg": round(self.calculate_co2_savings(generation_kwh), 1),
        }


# Plugin registry
_plugins: dict[str, CountryPlugin] = {}


def register_plugin(plugin: CountryPlugin) -> None:
    """Register a country plugin."""
    _plugins[plugin.constants.country_code] = plugin


def get_plugin(country_code: str) -> Optional[CountryPlugin]:
    """Get plugin by country code."""
    return _plugins.get(country_code.upper())


def get_plugin_for_location(lat: float, lon: float) -> CountryPlugin:
    """
    Get appropriate plugin for a geographic location.
    
    Uses simple bounding box detection for MVP.
    Falls back to global plugin if no specific match.
    """
    # Simple country detection based on coordinates
    # In production, use reverse geocoding API
    
    # Chile: -17.5 to -56 lat, -75.5 to -66.5 lon
    if -56 <= lat <= -17.5 and -75.5 <= lon <= -66.5:
        plugin = get_plugin("CL")
        if plugin:
            return plugin
    
    # Germany: 47 to 55 lat, 6 to 15 lon
    if 47 <= lat <= 55 and 6 <= lon <= 15:
        plugin = get_plugin("DE")
        if plugin:
            return plugin
    
    # Default to global plugin
    from app.plugins.countries.global_default import GlobalPlugin
    return GlobalPlugin()

