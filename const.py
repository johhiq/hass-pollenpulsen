"""Constants for the Pollenpulsen integration."""
from datetime import timedelta

# Domain and API endpoints
DOMAIN = "pollenpulsen"
BASE_URL = "https://api.pollenrapporten.se"
API_BASE_URL = f"{BASE_URL}/v1"
API_URL_FORECASTS = f"{API_BASE_URL}/forecasts"
API_URL_REGIONS = f"{API_BASE_URL}/regions"
API_URL_POLLEN_TYPES = f"{API_BASE_URL}/pollen-types"
API_URL_LEVEL_DEFINITIONS = f"{API_BASE_URL}/pollen-level-definitions"

# Configuration constants
CONF_REGION_ID = "region_id"
CONF_POLLEN_TYPES = "pollen_types"
CONF_NAME = "name"
DEFAULT_SCAN_INTERVAL = 3  # hours

# Misc constants
ATTRIBUTION = "Data provided by the Palynological Laboratory at the Swedish Museum of Natural History"