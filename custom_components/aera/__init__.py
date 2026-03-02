"""Aera Smart Diffuser integration for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import AeraCoordinator

if TYPE_CHECKING:
    from .ayla_api import AeraApi

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.FAN, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aera from a config entry."""
    # Import here to avoid loading ayla_api at startup
    from .ayla_api import AeraApi

    api = AeraApi(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    try:
        await api.login()
    except Exception as err:
        _LOGGER.error("Failed to login to Aera: %s", err)
        raise ConfigEntryAuthFailed("Invalid credentials") from err

    try:
        devices = await api.get_devices()
    except Exception as err:
        _LOGGER.error("Failed to get Aera devices: %s", err)
        raise ConfigEntryNotReady("Could not fetch devices") from err

    if not devices:
        _LOGGER.warning("No Aera devices found")
        return False

    coordinator = AeraCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: AeraCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

    return unload_ok
