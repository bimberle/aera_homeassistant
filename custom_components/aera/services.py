"""Services for Aera integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN, SESSION_DURATIONS
from .coordinator import AeraCoordinator

if TYPE_CHECKING:
    from .ayla_api import AeraDevice

_LOGGER = logging.getLogger(__name__)

SERVICE_START_SESSION = "start_session"
SERVICE_STOP_SESSION = "stop_session"
SERVICE_SET_FRAGRANCE = "set_fragrance"

ATTR_DURATION = "duration"
ATTR_FRAGRANCE_ID = "fragrance_id"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Aera integration."""

    async def _get_devices_from_call(call: ServiceCall) -> list["AeraDevice"]:
        """Get devices from service call."""
        entity_ids = call.data.get("entity_id", [])
        if isinstance(entity_ids, str):
            entity_ids = [entity_ids]

        entity_registry = er.async_get(hass)
        devices: list["AeraDevice"] = []

        for entry_id, coordinator in hass.data[DOMAIN].items():
            if not isinstance(coordinator, AeraCoordinator):
                continue
            for entity_id in entity_ids:
                entry = entity_registry.async_get(entity_id)
                if entry and entry.config_entry_id == entry_id:
                    # Extract DSN from unique_id (format: "{dsn}_fan")
                    dsn = entry.unique_id.replace("_fan", "")
                    if dsn in coordinator.devices:
                        devices.append(coordinator.devices[dsn])

        return devices

    async def async_start_session(call: ServiceCall) -> None:
        """Start a fragrance session."""
        duration_key = call.data[ATTR_DURATION]
        duration_minutes = SESSION_DURATIONS.get(duration_key)
        
        if duration_minutes is None:
            _LOGGER.error("Invalid duration: %s", duration_key)
            return

        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.start_session(duration_minutes)
            _LOGGER.info("Started %s session on %s", duration_key, device.name)

    async def async_stop_session(call: ServiceCall) -> None:
        """Stop the current session."""
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.stop_session()
            _LOGGER.info("Stopped session on %s", device.name)

    async def async_set_fragrance(call: ServiceCall) -> None:
        """Set fragrance on device."""
        fragrance_id = call.data[ATTR_FRAGRANCE_ID]
        
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.set_fragrance(fragrance_id)
            _LOGGER.info("Set fragrance %s on %s", fragrance_id, device.name)

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_SESSION,
        async_start_session,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_DURATION): vol.In(["2h", "4h", "8h"]),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_SESSION,
        async_stop_session,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FRAGRANCE,
        async_set_fragrance,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_FRAGRANCE_ID): cv.string,
            }
        ),
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_START_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_SET_FRAGRANCE)
