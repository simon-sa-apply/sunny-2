"""Country-specific regulatory plugins."""

from app.plugins.base import CountryPlugin, get_plugin_for_location

__all__ = ["CountryPlugin", "get_plugin_for_location"]

