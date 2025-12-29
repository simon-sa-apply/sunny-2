"""Country-specific regulatory plugins."""

from app.plugins.base import CountryPlugin, get_plugin_for_location
from app.plugins.countries import chile, germany, global_default

__all__ = ["CountryPlugin", "get_plugin_for_location"]

