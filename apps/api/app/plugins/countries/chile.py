"""Chile country plugin - Net Billing (Ley 21.118)."""

from app.plugins.base import CountryConstants, CountryPlugin, register_plugin


class ChilePlugin(CountryPlugin):
    """
    Chile-specific solar regulations.
    
    Based on:
    - Ley 21.118 (Net Billing)
    - Norma Técnica de Conexión y Operación
    - SEC regulations
    """

    @property
    def constants(self) -> CountryConstants:
        return CountryConstants(
            country_code="CL",
            country_name="Chile",
            data_tier="engineering",
            
            # Net Billing factor - value received for injected energy
            # Typically 70-90% of consumption price
            net_billing_factor=0.85,
            
            # Grid efficiency (transmission losses)
            grid_efficiency=0.97,
            
            # CO2 factor - Chile's grid is relatively clean
            # but still has thermal generation
            co2_factor_kg_per_kwh=0.42,
            
            # Regulatory reference
            regulatory_reference="Ley 21.118 - Net Billing",
            
            # Currency (standardized to USD)
            currency="USD",
            currency_symbol="$",
            
            # Average residential electricity price (USD/kWh)
            # ~CLP 175/kWh ≈ $0.18/kWh
            avg_electricity_price=0.18,
        )


# Register plugin on import
register_plugin(ChilePlugin())

