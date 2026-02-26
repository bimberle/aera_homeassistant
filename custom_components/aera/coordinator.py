"""DataUpdateCoordinator for Aera."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

if TYPE_CHECKING:
    from .ayla_api import AeraApi, AeraDevice

_LOGGER = logging.getLogger(__name__)


class AeraCoordinator(DataUpdateCoordinator[dict[str, "AeraDevice"]]):
    """Class to manage fetching Aera data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: "AeraApi",
        devices: list["AeraDevice"],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self._devices = {device.dsn: device for device in devices}

    @property
    def devices(self) -> dict[str, "AeraDevice"]:
        """Return all devices."""
        return self._devices

    async def _async_update_data(self) -> dict[str, "AeraDevice"]:
        """Fetch data from API."""
        try:
            for device in self._devices.values():
                await device.update()
            return self._devices
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Aera API: {err}") from err
