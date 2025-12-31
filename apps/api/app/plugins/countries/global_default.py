"""Global default plugin for countries without specific regulations."""

from typing import Any

from app.plugins.base import CountryConstants, CountryPlugin


class GlobalPlugin(CountryPlugin):
    """
    Default plugin for countries without specific solar regulations.

    Uses conservative global averages and prompts user for local values.
    """

    @property
    def constants(self) -> CountryConstants:
        return CountryConstants(
            country_code="GLOBAL",
            country_name="Global Default",
            data_tier="standard",

            # Conservative net billing assumption
            net_billing_factor=0.70,

            # Average grid efficiency
            grid_efficiency=0.95,

            # Global average CO2 factor
            co2_factor_kg_per_kwh=0.50,

            # No specific regulatory reference
            regulatory_reference="Generic estimation - verify local regulations",

            # Use USD as default
            currency="USD",
            currency_symbol="$",

            # Global average electricity price (varies widely)
            avg_electricity_price=0.15,
        )

    def calculate_savings(
        self,
        generation_kwh: float,
        custom_price: float | None = None,
    ) -> dict[str, Any]:
        """
        Calculate savings with emphasis on user-provided values.
        """
        result = super().calculate_savings(generation_kwh, custom_price)

        # Add advisory message for standard tier
        result["advisory"] = (
            "These calculations use global averages. "
            "For accurate results, please provide your local electricity price "
            "and verify applicable regulations in your region."
        )

        # Flag that user input would improve accuracy
        result["requires_user_input"] = custom_price is None

        return result

