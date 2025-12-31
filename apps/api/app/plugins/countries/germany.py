"""Germany country plugin - EEG and DIN V 18599."""

from app.plugins.base import CountryConstants, CountryPlugin, register_plugin


class GermanyPlugin(CountryPlugin):
    """
    Germany-specific solar regulations.

    Based on:
    - EEG (Erneuerbare-Energien-Gesetz)
    - DIN V 18599 (Energy efficiency calculation)
    - Feed-in tariff regulations
    """

    @property
    def constants(self) -> CountryConstants:
        return CountryConstants(
            country_code="DE",
            country_name="Germany",
            data_tier="engineering",

            # Net metering / feed-in factor
            # Germany has reduced feed-in tariffs over time
            net_billing_factor=0.08,  # Current low feed-in tariff

            # Grid efficiency
            grid_efficiency=0.98,

            # CO2 factor - Germany still uses coal/gas
            co2_factor_kg_per_kwh=0.35,

            # Regulatory reference
            regulatory_reference="EEG 2023 + DIN V 18599",

            # Currency (standardized to USD)
            currency="USD",
            currency_symbol="$",

            # Average residential electricity price (USD/kWh)
            # ~€0.35/kWh ≈ $0.38/kWh
            avg_electricity_price=0.38,
        )

    def calculate_savings(self, generation_kwh: float, custom_price=None):
        """
        Override savings for German self-consumption model.

        In Germany, self-consumption is more valuable than feed-in,
        so we prioritize avoided costs over injection revenue.
        """
        price = custom_price or self.constants.avg_electricity_price

        # Assume 70% self-consumption, 30% feed-in
        self_consumption_ratio = 0.70

        self_consumed = generation_kwh * self_consumption_ratio
        fed_in = generation_kwh * (1 - self_consumption_ratio)

        # Self-consumption saves at retail price
        self_consumption_value = self_consumed * price

        # Feed-in at low tariff
        feed_in_value = fed_in * self.constants.net_billing_factor

        total_value = self_consumption_value + feed_in_value

        return {
            "annual_savings": round(total_value, 2),
            "monthly_average": round(total_value / 12, 2),
            "currency": self.constants.currency,
            "currency_symbol": self.constants.currency_symbol,
            "price_per_kwh": price,
            "self_consumption_ratio": self_consumption_ratio,
            "self_consumption_value": round(self_consumption_value, 2),
            "feed_in_value": round(feed_in_value, 2),
            "co2_savings_kg": round(self.calculate_co2_savings(generation_kwh), 1),
        }


# Register plugin on import
register_plugin(GermanyPlugin())

