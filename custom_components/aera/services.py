"""Services for Aera integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv, entity_registry as er

from .const import DOMAIN, SESSION_DURATIONS
from .coordinator import AeraCoordinator

if TYPE_CHECKING:
    from .ayla_api import AeraDevice

_LOGGER = logging.getLogger(__name__)

SERVICE_START_SESSION = "start_session"
SERVICE_STOP_SESSION = "stop_session"
SERVICE_TURN_ON = "turn_on"
SERVICE_TURN_OFF = "turn_off"
SERVICE_SET_INTENSITY = "set_intensity"
SERVICE_SET_FRAGRANCE = "set_fragrance"
SERVICE_SET_ROOM_NAME = "set_room_name"
SERVICE_GET_SCHEDULES = "get_schedules"
SERVICE_CREATE_SCHEDULE = "create_schedule"
SERVICE_UPDATE_SCHEDULE = "update_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_TOGGLE_SCHEDULE = "toggle_schedule"

ATTR_DURATION = "duration"
ATTR_FRAGRANCE_ID = "fragrance_id"
ATTR_ROOM_NAME = "room_name"
ATTR_SCHEDULE_KEY = "schedule_key"
ATTR_SCHEDULE_NAME = "schedule_name"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_DAYS = "days"
ATTR_INTENSITY = "intensity"
ATTR_ACTIVE = "active"


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

    async def async_turn_on(call: ServiceCall) -> None:
        """Turn the diffuser on."""
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.turn_on()
            _LOGGER.info("Turned on %s", device.name)

    async def async_turn_off(call: ServiceCall) -> None:
        """Turn the diffuser off."""
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.turn_off()
            _LOGGER.info("Turned off %s", device.name)

    async def async_set_intensity(call: ServiceCall) -> None:
        """Set the fragrance intensity."""
        intensity = call.data[ATTR_INTENSITY]
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.set_intensity(intensity)
            _LOGGER.info("Set intensity to %d on %s", intensity, device.name)

    async def async_set_fragrance(call: ServiceCall) -> None:
        """Set fragrance on device."""
        fragrance_id = call.data[ATTR_FRAGRANCE_ID]
        
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.set_fragrance(fragrance_id)
            _LOGGER.info("Set fragrance %s on %s", fragrance_id, device.name)

    async def async_set_room_name(call: ServiceCall) -> None:
        """Set room name on device."""
        room_name = call.data[ATTR_ROOM_NAME]
        
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.set_room_name(room_name)
            _LOGGER.info("Set room name '%s' on %s", room_name, device.name)

    async def async_get_schedules(call: ServiceCall) -> dict:
        """Get all schedules for a device."""
        devices = await _get_devices_from_call(call)
        result = {}
        for device in devices:
            schedules = await device.get_schedules()
            result[device.dsn] = [
                {
                    "key": s.key,
                    "name": s.display_name,
                    "active": s.active,
                    "start_time": s.start_time_each_day[:5],  # HH:MM
                    "end_time": s.end_time_each_day[:5],      # HH:MM
                    "days": s.days_of_week,
                    "actions": [
                        {"name": a.name, "value": a.value}
                        for a in s.actions
                    ],
                }
                for s in schedules
            ]
            _LOGGER.info("Got %d schedules for %s", len(schedules), device.name)
        return result

    async def async_create_schedule(call: ServiceCall) -> dict:
        """Create a new schedule."""
        schedule_name = call.data[ATTR_SCHEDULE_NAME]
        start_time = call.data.get(ATTR_START_TIME, "08:00")
        end_time = call.data.get(ATTR_END_TIME, "22:00")
        days = call.data.get(ATTR_DAYS, [2, 3, 4, 5, 6])  # Mon-Fri
        intensity = call.data.get(ATTR_INTENSITY, 5)
        active = call.data.get(ATTR_ACTIVE, True)
        
        devices = await _get_devices_from_call(call)
        result = {}
        for device in devices:
            schedule = await device.create_schedule(
                name=schedule_name,
                start_time=start_time,
                end_time=end_time,
                days=days,
                intensity=intensity,
                active=active,
            )
            result[device.dsn] = {"key": schedule.key, "name": schedule.display_name}
            _LOGGER.info("Created schedule '%s' on %s", schedule_name, device.name)
        return result

    async def async_update_schedule(call: ServiceCall) -> dict:
        """Update an existing schedule."""
        schedule_key = call.data[ATTR_SCHEDULE_KEY]
        schedule_name = call.data.get(ATTR_SCHEDULE_NAME)
        start_time = call.data.get(ATTR_START_TIME)
        end_time = call.data.get(ATTR_END_TIME)
        days = call.data.get(ATTR_DAYS)
        intensity = call.data.get(ATTR_INTENSITY)
        active = call.data.get(ATTR_ACTIVE)
        
        devices = await _get_devices_from_call(call)
        result = {}
        for device in devices:
            schedule = await device.update_schedule(
                schedule_key=schedule_key,
                name=schedule_name,
                start_time=start_time,
                end_time=end_time,
                days=days,
                intensity=intensity,
                active=active,
            )
            result[device.dsn] = {"key": schedule.key, "name": schedule.display_name}
            _LOGGER.info("Updated schedule %d on %s", schedule_key, device.name)
        return result

    async def async_delete_schedule(call: ServiceCall) -> None:
        """Delete a schedule."""
        schedule_key = call.data[ATTR_SCHEDULE_KEY]
        
        devices = await _get_devices_from_call(call)
        for device in devices:
            await device.delete_schedule(schedule_key)
            _LOGGER.info("Deleted schedule %d on %s", schedule_key, device.name)

    async def async_toggle_schedule(call: ServiceCall) -> dict:
        """Enable or disable a schedule."""
        schedule_key = call.data[ATTR_SCHEDULE_KEY]
        active = call.data[ATTR_ACTIVE]
        
        devices = await _get_devices_from_call(call)
        result = {}
        for device in devices:
            schedule = await device.toggle_schedule(schedule_key, active)
            result[device.dsn] = {"key": schedule.key, "active": schedule.active}
            _LOGGER.info("Toggled schedule %d to %s on %s", schedule_key, active, device.name)
        return result

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
        SERVICE_TURN_ON,
        async_turn_on,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TURN_OFF,
        async_turn_off,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_INTENSITY,
        async_set_intensity,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_INTENSITY): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10)
                ),
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ROOM_NAME,
        async_set_room_name,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_ROOM_NAME): cv.string,
            }
        ),
    )

    # Schedule services
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SCHEDULES,
        async_get_schedules,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CREATE_SCHEDULE,
        async_create_schedule,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_SCHEDULE_NAME): cv.string,
                vol.Optional(ATTR_START_TIME, default="08:00"): cv.string,
                vol.Optional(ATTR_END_TIME, default="22:00"): cv.string,
                vol.Optional(ATTR_DAYS, default=[2, 3, 4, 5, 6]): vol.All(
                    cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]
                ),
                vol.Optional(ATTR_INTENSITY, default=5): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10)
                ),
                vol.Optional(ATTR_ACTIVE, default=True): cv.boolean,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_SCHEDULE,
        async_update_schedule,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_SCHEDULE_KEY): vol.Coerce(int),
                vol.Optional(ATTR_SCHEDULE_NAME): cv.string,
                vol.Optional(ATTR_START_TIME): cv.string,
                vol.Optional(ATTR_END_TIME): cv.string,
                vol.Optional(ATTR_DAYS): vol.All(
                    cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]
                ),
                vol.Optional(ATTR_INTENSITY): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10)
                ),
                vol.Optional(ATTR_ACTIVE): cv.boolean,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_SCHEDULE,
        async_delete_schedule,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_SCHEDULE_KEY): vol.Coerce(int),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_SCHEDULE,
        async_toggle_schedule,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_ids,
                vol.Required(ATTR_SCHEDULE_KEY): vol.Coerce(int),
                vol.Required(ATTR_ACTIVE): cv.boolean,
            }
        ),
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_START_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_TURN_ON)
    hass.services.async_remove(DOMAIN, SERVICE_TURN_OFF)
    hass.services.async_remove(DOMAIN, SERVICE_SET_INTENSITY)
    hass.services.async_remove(DOMAIN, SERVICE_SET_FRAGRANCE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_ROOM_NAME)
    hass.services.async_remove(DOMAIN, SERVICE_GET_SCHEDULES)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_TOGGLE_SCHEDULE)
