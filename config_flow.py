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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_NAME
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL,
    CONF_REGION_ID,
    CONF_POLLEN_TYPES,
    API_URL_REGIONS,
    API_URL_POLLEN_TYPES
)
from .api import PollenPulsenApiClient, PollenPulsenApiClientError

_LOGGER = logging.getLogger(__name__)

class PollenpulsenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollenpulsen."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
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
                # Validate the user input
                # ...
                
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            except PollenPulsenApiClientError as error:
                _LOGGER.error("Error connecting to the API: %s", error)
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
                
        except PollenPulsenApiClientError as error:
            _LOGGER.error("Error getting regions: %s", error)
            errors["base"] = "cannot_connect"
            regions = {}
            
        # Show form to select region
        region_schema = vol.Schema({
            vol.Required(CONF_REGION_ID): vol.In(regions),
            vol.Required(CONF_NAME, default="Pollenpulsen"): str,
            vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=24)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=region_schema,
            errors=errors,
        )

    async def async_step_pollen_types(self, user_input=None) -> FlowResult:
        """Handle the pollen types selection step.
        
        Fetch available pollen types from the API and let the user select which ones to monitor.
        """
        errors = {}

        # Fetch available pollen types from API
        try:
            pollen_types = await self.api_client.get_pollen_types()
            
            if not pollen_types:
                errors["base"] = "empty_pollen_types"
                _LOGGER.error("No pollen types received from API")
                return self.async_show_form(
                    step_id="pollen_types",
                    data_schema=vol.Schema({}),
                    errors=errors,
                    description_placeholders={"error": "No pollen types available from the API."}
                )
                
        except aiohttp.ClientError as err:
            errors["base"] = "cannot_connect"
            _LOGGER.error("Connection error while fetching pollen types: %s", err)
            return self.async_show_form(
                step_id="pollen_types",
                data_schema=vol.Schema({}),
                errors=errors,
                description_placeholders={"error": f"Connection error: {err}"}
            )
        except asyncio.TimeoutError:
            errors["base"] = "timeout"
            _LOGGER.error("Timeout while fetching pollen types")
            return self.async_show_form(
                step_id="pollen_types",
                data_schema=vol.Schema({}),
                errors=errors,
                description_placeholders={"error": "Connection timed out."}
            )
        except Exception as err:  # pylint: disable=broad-except
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected error while fetching pollen types: %s", err)
            return self.async_show_form(
                step_id="pollen_types",
                data_schema=vol.Schema({}),
                errors=errors,
                description_placeholders={"error": f"Unexpected error: {err}"}
            )

        if user_input is not None:
            # Combine data from both steps
            self.data.update(user_input)
            
            # Check if this region is already configured
            await self.async_set_unique_id(f"pollenpulsen_{self.data[CONF_REGION_ID]}")
            self._abort_if_unique_id_configured()
            
            # Get region name for the title
            try:
                regions = await self.api_client.get_regions()
                region_name = regions.get(self.data[CONF_REGION_ID], "Unknown")
            except Exception:  # pylint: disable=broad-except
                # Fallback to using region ID if we can't get the name
                region_name = self.data[CONF_REGION_ID]
            
            return self.async_create_entry(
                title=f"Pollenpulsen {region_name}",
                data=self.data
            )

        # Show form to select pollen types
        pollen_schema = vol.Schema({
            vol.Required(CONF_POLLEN_TYPES, default=list(pollen_types.keys())): cv.multi_select(pollen_types),
        })

        return self.async_show_form(
            step_id="pollen_types",
            data_schema=pollen_schema,
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
        self._config_entry = config_entry
        self.api_client = None

    async def async_step_init(self, user_input=None):
        """Manage the options.
        
        Allow the user to update scan interval and selected pollen types.
        """
        errors = {}
        
        if not self.api_client:
            self.api_client = PollenPulsenApiClient(self.hass)
            self.api_client.region_id = self._config_entry.data.get(CONF_REGION_ID, "")

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Fetch available pollen types from API
        try:
            pollen_types = await self.api_client.get_pollen_types()
            
            if not pollen_types:
                errors["base"] = "empty_pollen_types"
                _LOGGER.error("No pollen types received from API during options flow")
                
        except aiohttp.ClientError as err:
            errors["base"] = "cannot_connect"
            _LOGGER.error("Connection error while fetching pollen types in options flow: %s", err)
            pollen_types = {}
        except asyncio.TimeoutError:
            errors["base"] = "timeout"
            _LOGGER.error("Timeout while fetching pollen types in options flow")
            pollen_types = {}
        except Exception as err:  # pylint: disable=broad-except
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected error while fetching pollen types in options flow: %s", err)
            pollen_types = {}

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self._config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
        }
        
        if pollen_types:
            options[vol.Optional(
                CONF_POLLEN_TYPES,
                default=self._config_entry.data.get(CONF_POLLEN_TYPES, list(pollen_types.keys()))
            )] = cv.multi_select(pollen_types)

        return self.async_show_form(
            step_id="init", 
            data_schema=vol.Schema(options),
            errors=errors,
            description_placeholders={"error": "Could not fetch pollen types. You can still update the scan interval."} if errors else None
        )