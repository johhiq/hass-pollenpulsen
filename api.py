"""API client for Pollenrapporten.

This module provides a client for interacting with the Pollenrapporten API.
It handles fetching forecasts, regions, and pollen types.
"""
import logging
import aiohttp
import async_timeout
import asyncio
import socket
from datetime import datetime
from typing import Dict, List, Optional, Any
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL_FORECASTS, API_URL_REGIONS, API_URL_POLLEN_TYPES

_LOGGER = logging.getLogger(__name__)

class PollenPulsenApiClientError(Exception):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the exception.
        
        Args:
            message: The error message
            status_code: The HTTP status code if applicable
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class PollenPulsenApiClient:
    """API client for Pollenpulsen."""

    def __init__(self, hass):
        """Initialize the API client."""
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self.region_id = ""
        self._pollen_types_cache = {}
        self._regions_cache = {}
        _LOGGER.debug("Initialized PollenPulsen API client")

    async def get_forecasts(self) -> Dict[str, Any]:
        """Get pollen forecasts for the configured region.
        
        Returns:
            A dictionary containing forecast data including pollen levels,
            start and end dates, and forecast text.
            
        Raises:
            PollenPulsenApiClientError: If there's an error fetching the data
            aiohttp.ClientError: If there's a connection error
            asyncio.TimeoutError: If the request times out
        """
        try:
            url = f"{API_URL_FORECASTS}?region_id={self.region_id}&current=true"
            _LOGGER.debug("Fetching forecast data from: %s", url)
            
            async with async_timeout.timeout(10):
                response = await self._session.get(url)
                
                _LOGGER.debug("Forecast API response status: %s", response.status)
                
                if response.status >= 400:
                    error_text = await response.text()
                    _LOGGER.error(
                        "HTTP error %d while fetching forecast data: %s", 
                        response.status, 
                        error_text
                    )
                    raise PollenPulsenApiClientError(
                        f"HTTP error {response.status}: {error_text}", 
                        response.status
                    )
                
                data = await response.json()
                _LOGGER.debug("Received forecast data: %s", data)
                
                if not data:
                    _LOGGER.error("Empty response received from API")
                    raise PollenPulsenApiClientError("Empty response received from API")
                
                if "items" not in data or not data["items"]:
                    _LOGGER.error("No forecast items received from API")
                    raise PollenPulsenApiClientError("No forecast items received from API")
                
                # Process the forecast data
                forecast = data["items"][0]
                result = {
                    "start_date": forecast.get("startDate"),
                    "end_date": forecast.get("endDate"),
                    "text": forecast.get("text", ""),
                    "pollen_levels": {}
                }
                
                # Get today's date in the format used by the API
                today = datetime.now().strftime("%Y-%m-%d")
                _LOGGER.debug("Processing forecast data for date: %s", today)
                
                # Extract pollen levels for today
                if "levelSeries" in forecast:
                    for level_data in forecast["levelSeries"]:
                        if today in level_data.get("time", ""):
                            pollen_id = level_data.get("pollenId")
                            level = level_data.get("level")
                            if pollen_id and level is not None:
                                result["pollen_levels"][pollen_id] = level
                
                _LOGGER.debug("Processed forecast data: %s", result)
                return result
                
        except aiohttp.ClientError as error:
            _LOGGER.error("Connection error fetching forecast data: %s", error)
            raise
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching forecast data from: %s", url)
            raise
        except PollenPulsenApiClientError:
            raise
        except Exception as error:
            _LOGGER.exception("Unexpected error fetching forecast data: %s", error)
            raise PollenPulsenApiClientError(f"Unexpected error: {error}")

    async def get_regions(self) -> Dict[str, str]:
        """Get available regions from the API."""
        # Return cached data if available
        if self._regions_cache:
            _LOGGER.debug("Returning cached regions data")
            return self._regions_cache

        try:
            _LOGGER.debug("Fetching regions from %s", API_URL_REGIONS)
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    url=API_URL_REGIONS,
                    headers={
                        "Content-Type": "application/json",
                    },
                )
                
                _LOGGER.debug("Regions API response status: %s", response.status)
                
                if response.status != 200:
                    _LOGGER.error("Failed to get regions, status code: %s", response.status)
                    return {}
                    
                data = await response.json()
                _LOGGER.debug("Received regions data: %s", data)
                
                if "items" not in data:
                    _LOGGER.error("No 'items' key in regions response: %s", data)
                    return {}
                    
                # Create a dictionary with region_id as key and region_name as value
                regions = {region["id"]: region["name"] for region in data["items"]}
                _LOGGER.debug("Parsed regions: %s", regions)
                
                if not regions:
                    _LOGGER.error("No regions found in API response")
                else:
                    # Cache the successful response
                    self._regions_cache = regions
                    
                return regions
                
        except asyncio.TimeoutError as error:
            _LOGGER.error("Timeout error fetching regions: %s", error)
            raise PollenPulsenApiClientError("Timeout error fetching regions") from error
        except (KeyError, TypeError) as error:
            _LOGGER.error("Error parsing regions response: %s", error)
            raise PollenPulsenApiClientError("Error parsing regions response") from error
        except (aiohttp.ClientError, socket.gaierror) as error:
            _LOGGER.error("Error fetching regions: %s", error)
            raise PollenPulsenApiClientError("Error fetching regions") from error
        except Exception as error:
            _LOGGER.error("Unexpected error while fetching regions: %s", error)
            raise PollenPulsenApiClientError("Unexpected error while fetching regions") from error

    async def get_pollen_types(self) -> Dict[str, str]:
        """Get available pollen types from the API.
        
        Returns:
            A dictionary mapping pollen type IDs to pollen type names.
            
        Raises:
            PollenPulsenApiClientError: If there's an error fetching the data
            aiohttp.ClientError: If there's a connection error
            asyncio.TimeoutError: If the request times out
        """
        # Return cached data if available
        if self._pollen_types_cache:
            _LOGGER.debug("Returning cached pollen types data")
            return self._pollen_types_cache
            
        try:
            _LOGGER.debug("Fetching pollen types from %s", API_URL_POLLEN_TYPES)
            async with async_timeout.timeout(10):
                response = await self._session.get(API_URL_POLLEN_TYPES)
                
                _LOGGER.debug("Pollen types API response status: %s", response.status)
                
                if response.status >= 400:
                    error_text = await response.text()
                    _LOGGER.error(
                        "HTTP error %d while fetching pollen types: %s", 
                        response.status, 
                        error_text
                    )
                    raise PollenPulsenApiClientError(
                        f"HTTP error {response.status}: {error_text}", 
                        response.status
                    )
                
                data = await response.json()
                _LOGGER.debug("Received pollen types data: %s", data)
                
                if not data or "items" not in data:
                    _LOGGER.error("Invalid or empty response received when fetching pollen types")
                    raise PollenPulsenApiClientError("Invalid or empty response when fetching pollen types")
                
                # Create a mapping of pollen type IDs to names from the items array
                pollen_types = {item["id"]: item["name"] for item in data["items"]}
                _LOGGER.debug("Parsed pollen types: %s", pollen_types)
                
                if not pollen_types:
                    _LOGGER.error("No pollen types found in API response")
                    raise PollenPulsenApiClientError("No pollen types found in API response")
                
                # Cache the successful response
                self._pollen_types_cache = pollen_types
                return pollen_types
                
        except aiohttp.ClientError as error:
            _LOGGER.error("Connection error fetching pollen types: %s", error)
            raise
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching pollen types from: %s", API_URL_POLLEN_TYPES)
            raise
        except PollenPulsenApiClientError:
            raise
        except Exception as error:
            _LOGGER.exception("Unexpected error fetching pollen types: %s", error)
            raise PollenPulsenApiClientError(f"Unexpected error: {error}")
