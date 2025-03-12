"""Sensor platform for Pollenpulsen integration.

This module provides sensor entities for pollen levels and forecasts.
"""
from datetime import timedelta, datetime
import logging
from typing import Any, Dict
import async_timeout
import zoneinfo

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    ATTRIBUTION,
    CONF_REGION_ID,
    DEFAULT_SCAN_INTERVAL,
    API_URL_LEVEL_DEFINITIONS,
)
from .api import PollenPulsenApiClient, PollenPulsenApiClientError

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pollenpulsen sensor from a config entry."""
    region_id = entry.data[CONF_REGION_ID]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    api_client = PollenPulsenApiClient(hass)
    api_client.region_id = region_id
    
    try:
        regions = await api_client.get_regions()
        region_name = regions.get(region_id, region_id)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error fetching region names: %s", err)
        region_name = region_id
    
    coordinator = PollenDataCoordinator(
        hass,
        api_client=api_client,
        update_interval=timedelta(hours=scan_interval)
    )
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error during initial data refresh: %s", err)
    
    async_add_entities([PollenForecastSensor(coordinator, region_id, region_name)])

class PollenDataCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch pollen data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: PollenPulsenApiClient,
        update_interval: timedelta
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Pollen Data",
            update_interval=update_interval,
        )
        self.api_client = api_client
        self._session = async_get_clientsession(hass)
        self._last_successful_data = {}
        self._level_definitions = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API."""
        try:
            # Fetch level definitions if we don't have them yet
            if not self._level_definitions:
                try:
                    async with async_timeout.timeout(10):
                        response = await self._session.get(API_URL_LEVEL_DEFINITIONS)
                        if response.status == 200:
                            data = await response.json()
                            if "items" in data:
                                self._level_definitions = {
                                    item["level"]: item["name"]
                                    for item in data["items"]
                                }
                                _LOGGER.debug("Fetched pollen level definitions: %s", self._level_definitions)
                        else:
                            _LOGGER.warning(
                                "Failed to fetch level definitions, status: %s", 
                                response.status
                            )
                except Exception as err:
                    _LOGGER.warning("Error fetching level definitions: %s", err)

            # Fetch pollen types if we don't have them
            if not hasattr(self, '_pollen_types'):
                try:
                    self._pollen_types = await self.api_client.get_pollen_types()
                except Exception as err:
                    _LOGGER.warning("Error fetching pollen types: %s", err)
                    self._pollen_types = {}

            # Fetch regular forecast data
            data = await self.api_client.get_forecasts()
            if data:
                # Add level definitions and pollen types to the data
                data["level_definitions"] = self._level_definitions
                data["pollen_types"] = self._pollen_types
                self._last_successful_data = data
            return data

        except PollenPulsenApiClientError as err:
            if self._last_successful_data:
                _LOGGER.warning(
                    "Error fetching data: %s. Using cached data from last successful update.",
                    err
                )
                return self._last_successful_data
            raise UpdateFailed(f"API error: {err}") from err
        except Exception as err:
            if self._last_successful_data:
                _LOGGER.warning(
                    "Unexpected error fetching data: %s. Using cached data from last successful update.",
                    err
                )
                return self._last_successful_data
            raise UpdateFailed(f"Error fetching data: {err}") from err

class PollenForecastSensor(CoordinatorEntity, SensorEntity):
    """Main sensor entity for pollen forecast."""

    def __init__(
        self,
        coordinator: PollenDataCoordinator,
        region_id: str,
        region_name: str
    ) -> None:
        """Initialize the forecast sensor."""
        super().__init__(coordinator)
        self._region_id = region_id
        self._region_name = region_name
        
        self._attr_name = f"Pollenprognos {region_name}"
        self._attr_unique_id = f"pollenprognos_{region_name.lower()}"
        self._attr_icon = "mdi:flower-pollen"
        
    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "unavailable"
        
        if self.coordinator.data.get("pollen_levels"):
            return "active"
        return "no_data"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes with the structured data format."""
        if not self.coordinator.data:
            return {}
            
        attributes = {
            "last_updated": datetime.now(zoneinfo.ZoneInfo("Europe/Stockholm")).isoformat(),
            "forecast": {
                "text": self.coordinator.data.get("text", "Ingen prognos tillgänglig"),
                "start_date": self.coordinator.data.get("start_date"),
                "end_date": self.coordinator.data.get("end_date"),
                "region": self._region_name
            },
            "pollen_levels": [],
            "metadata": {
                "attribution": ATTRIBUTION,
                "last_update_success": self.coordinator.last_update_success
            }
        }
        
        if pollen_levels := self.coordinator.data.get("pollen_levels", {}):
            pollen_types = self.coordinator.data.get("pollen_types", {})
            level_definitions = self.coordinator.data.get("level_definitions", {})
            
            for pollen_id, level in pollen_levels.items():
                pollen_info = {
                    "type": pollen_types.get(pollen_id, pollen_id),
                    "type_id": pollen_id,
                    "level": level,
                    "description": level_definitions.get(level, f"Okänd nivå: {level}")
                }
                attributes["pollen_levels"].append(pollen_info)
        
        # Sort pollen levels alphabetically by type
        attributes["pollen_levels"].sort(key=lambda x: x["type"])
        
        return attributes