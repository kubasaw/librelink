"""DataUpdateCoordinator for LibreLink."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import LibreLinkAPI
from .const import DOMAIN, LOGGER, REFRESH_RATE_MIN


class LibreLinkDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API. single endpoint."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: LibreLinkAPI,
    ) -> None:
        """Initialize."""
        self.api: LibreLinkAPI = api

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=REFRESH_RATE_MIN),
        )

    async def _async_update_data(self):
        """Update data via library."""
        return await self.api.async_get_data()
