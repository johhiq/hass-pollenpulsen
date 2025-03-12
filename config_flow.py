"""Config flow for Pollenpulsen integration.

This module handles the configuration flow for the Pollenpulsen integration,
including fetching available regions and pollen types from the API.
"""
import logging
import voluptuous as vol
import aiohttp
import asyncio

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_NAME
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL,
    CONF_REGION_ID,
)
from .api import PollenPulsenApiClient, PollenPulsenApiClientError

_LOGGER = logging.getLogger(__name__)

class PollenpulsenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollenpulsen."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.api_client = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step.
        
        Fetch available regions from the API and let the user select one.
        """
        errors = {}

        if self.api_client is None:
            self.api_client = PollenPulsenApiClient(self.hass)

        if user_input is not None:
            try:
                # Check if this region is already configured
                await self.async_set_unique_id(f"pollenpulsen_{user_input[CONF_REGION_ID]}")
                self._abort_if_unique_id_configured()
                
                # Get region name for the title
                try:
                    regions = await self.api_client.get_regions()
                    region_name = regions.get(user_input[CONF_REGION_ID], "Unknown")
                except Exception:  # pylint: disable=broad-except
                    region_name = user_input[CONF_REGION_ID]
                
                return self.async_create_entry(
                    title=f"Pollenpulsen {region_name}",
                    data={
                        CONF_REGION_ID: user_input[CONF_REGION_ID],
                        CONF_NAME: user_input[CONF_NAME],
                    }
                )
                
            except PollenPulsenApiClientError:
                errors["base"] = "cannot_connect"
                
        # Get regions from API
        try:
            regions = await self.api_client.get_regions()
            _LOGGER.debug("Received regions: %s", regions)
            
            if not regions:
                _LOGGER.error("No regions received from API")
                errors["base"] = "no_regions"
                
            # Sort regions by creating a new OrderedDict
            regions = dict(sorted(regions.items(), key=lambda x: x[1]))
                
        except PollenPulsenApiClientError:
            _LOGGER.error("Error getting regions")
            errors["base"] = "cannot_connect"
            regions = {}
            
        # Show form to select region
        region_schema = vol.Schema({
            vol.Required(CONF_REGION_ID): vol.In(regions),
            vol.Required(CONF_NAME, default="Pollenpulsen"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=region_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Pollenpulsen integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options.
        
        Allow the user to update scan interval and selected pollen types.
        """
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
        }

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(options),
        )