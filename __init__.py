"""Pollenpulsen integration for Home Assistant.

This integration provides sensors for pollen forecasts from Pollenrapporten.
"""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollenpulsen from a config entry.
    
    Args:
        hass: The Home Assistant instance
        entry: The config entry
        
    Returns:
        True if setup was successful
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    Args:
        hass: The Home Assistant instance
        entry: The config entry to unload
        
    Returns:
        True if unload was successful
    """
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update.
    
    Args:
        hass: The Home Assistant instance
        entry: The config entry that was updated
    """
    await hass.config_entries.async_reload(entry.entry_id)