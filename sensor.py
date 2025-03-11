"""Sensor platform for Pollenpulsen integration.

This module provides sensor entities for pollen levels and forecasts.
"""
from datetime import timedelta, datetime
import logging
from typing import Any, Dict, List, Optional
import async_timeout
import zoneinfo

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
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
    CONF_POLLEN_TYPES,
    DEFAULT_SCAN_INTERVAL,
    API_URL_LEVEL_DEFINITIONS,
)
from .api import PollenPulsenApiClient, PollenPulsenApiClientError

_LOGGER = logging.getLogger(__name__)

# Translation keys
KEY_NO_DATA = "no_data_available"
KEY_NO_FORECAST = "no_forecast_available"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pollenpulsen sensor from a config entry."""
    region_id = entry.data[CONF_REGION_ID]
    pollen_types = entry.data.get(CONF_POLLEN_TYPES, [])
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    api_client = PollenPulsenApiClient(hass)
    api_client.region_id = region_id
    
    try:
        regions = await api_client.get_regions()
        region_name = regions.get(region_id, region_id)
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error fetching region names: %s", err)
        region_name = region_id
    
    try:
        pollen_types_data = await api_client.get_pollen_types()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error fetching pollen type names: %s", err)
        pollen_types_data = {}
    
    coordinator = PollenDataCoordinator(
        hass,
        api_client=api_client,
        update_interval=timedelta(hours=scan_interval)
    )
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Error during initial data refresh: %s", err)
    
    entities = []
    
    # Create a forecast sensor
    entities.append(PollenForecastSensor(coordinator, region_id, region_name))
    
    # Create sensors for each selected pollen type
    for pollen_id in pollen_types:
        pollen_name = pollen_types_data.get(pollen_id, pollen_id)
        entities.append(PollenSensor(coordinator, pollen_id, region_id, pollen_name, region_name))
    
    async_add_entities(entities)

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

class PollenSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for pollen levels."""

    def __init__(
        self,
        coordinator: PollenDataCoordinator,
        pollen_id: str,
        region_id: str,
        pollen_name: str,
        region_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._pollen_id = pollen_id
        self._region_id = region_id
        self._pollen_name = pollen_name
        self._region_name = region_name
        
        self._attr_name = f"{pollen_name}pollen {region_name}"
        self._attr_unique_id = f"pollen_{region_id}_{pollen_id}"
        self._attr_attribution = ATTRIBUTION
        self._attr_icon = "mdi:flower-pollen"
        self._attr_native_unit_of_measurement = "level"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success or 
            bool(self.coordinator._last_successful_data)
        )
        
    @property
    def native_value(self) -> Optional[int]:
        """Return the state of the sensor."""
        if not self.coordinator.data or "pollen_levels" not in self.coordinator.data:
            return None
        return self.coordinator.data["pollen_levels"].get(self._pollen_id)
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
        attributes = {
            "start_date": self.coordinator.data.get("start_date"),
            "end_date": self.coordinator.data.get("end_date"),
            "region": self._region_name,
            "last_update_success": self.coordinator.last_update_success
        }

        # Add current pollen level description
        level = self.coordinator.data.get("pollen_levels", {}).get(self._pollen_id)
        if level is not None and "level_definitions" in self.coordinator.data:
            attributes["level_description"] = self.coordinator.data["level_definitions"].get(
                level, f"Okänd nivå: {level}"
            )
        
        return attributes

class PollenForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor entity for pollen forecast text."""

    def __init__(
        self,
        coordinator: PollenDataCoordinator,
        region_id: str,
        region_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._region_id = region_id
        self._region_name = region_name
        
        self._attr_name = f"Pollenprognos {region_name}"
        self._attr_unique_id = f"pollenprognos_{region_name.lower()}"
        self._attr_attribution = ATTRIBUTION
        self._attr_icon = "mdi:text-box"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success or 
            bool(self.coordinator._last_successful_data)
        )
        
    @property
    def native_value(self) -> Optional[datetime]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        date_str = self.coordinator.data.get("start_date")
        if not date_str:
            return None
            
        try:
            # Konvertera datumsträngen till datetime med tidszon
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Stockholm"))
        except (ValueError, TypeError):
            _LOGGER.error("Failed to parse date: %s", date_str)
            return None
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
        attributes = {
            "forecast_text": self.coordinator.data.get("text", "Ingen prognos tillgänglig"),
            "end_date": self.coordinator.data.get("end_date"),
            "region": self._region_name,
            "last_update_success": self.coordinator.last_update_success
        }
        
        # Add image URLs for all regions if available
        if images := self.coordinator.data.get("images", []):
            pollen_types = self.coordinator.data.get("pollen_types", {})
            for image in images:
                if pollen_id := image.get("pollenId"):
                    pollen_name = pollen_types.get(pollen_id, pollen_id)
                    if url := image.get("url"):
                        attributes[f"map_url_{pollen_name}"] = url
        
        # Add pollen levels with names and descriptions if available
        if pollen_levels := self.coordinator.data.get("pollen_levels", {}):
            pollen_types = self.coordinator.data.get("pollen_types", {})
            level_definitions = self.coordinator.data.get("level_definitions", {})
            
            for pollen_id, level in pollen_levels.items():
                pollen_name = pollen_types.get(pollen_id, pollen_id)
                attributes[f"Pollen {pollen_name}"] = level
                if level is not None:
                    attributes[f"Pollen {pollen_name} description"] = level_definitions.get(
                        level, f"Okänd nivå: {level}"
                    )
        
        return attributes