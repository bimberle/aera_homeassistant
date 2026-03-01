"""Services for Aera integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.helpers import config_validation as cv, service

from .const import DOMAIN, SESSION_DURATIONS

if TYPE_CHECKING:
    from .fan import AeraFan

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_START_SESSION = "start_session"
SERVICE_STOP_SESSION = "stop_session"
SERVICE_SET_INTENSITY = "set_intensity"
SERVICE_SET_FRAGRANCE = "set_fragrance"
SERVICE_SET_ROOM_NAME = "set_room_name"
SERVICE_GET_SCHEDULES = "get_schedules"
SERVICE_REFRESH_SCHEDULES = "refresh_schedules"
SERVICE_CREATE_SCHEDULE = "create_schedule"
SERVICE_UPDATE_SCHEDULE = "update_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_TOGGLE_SCHEDULE = "toggle_schedule"

# Service attribute names
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


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Aera integration."""

    # Start Session
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_START_SESSION,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_DURATION): vol.In(["2h", "4h", "8h"]),
        },
        func="async_start_session",
    )

    # Stop Session
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_STOP_SESSION,
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_stop_session",
    )

    # Set Intensity
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_SET_INTENSITY,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_INTENSITY): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            ),
        },
        func="async_set_intensity_service",
    )

    # Set Fragrance
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_SET_FRAGRANCE,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_FRAGRANCE_ID): cv.string,
        },
        func="async_set_fragrance",
    )

    # Set Room Name
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_SET_ROOM_NAME,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_ROOM_NAME): cv.string,
        },
        func="async_set_room_name",
    )

    # Get Schedules
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_GET_SCHEDULES,
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_get_schedules",
        supports_response=SupportsResponse.ONLY,
    )

    # Refresh Schedules (invalidate cache and reload)
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_REFRESH_SCHEDULES,
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_refresh_schedules",
    )

    # Create Schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_CREATE_SCHEDULE,
        entity_domain=FAN_DOMAIN,
        schema={
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
        },
        func="async_create_schedule",
    )

    # Update Schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_UPDATE_SCHEDULE,
        entity_domain=FAN_DOMAIN,
        schema={
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
        },
        func="async_update_schedule",
    )

    # Delete Schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_DELETE_SCHEDULE,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_SCHEDULE_KEY): vol.Coerce(int),
        },
        func="async_delete_schedule",
    )

    # Toggle Schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        SERVICE_TOGGLE_SCHEDULE,
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required(ATTR_SCHEDULE_KEY): vol.Coerce(int),
            vol.Required(ATTR_ACTIVE): cv.boolean,
        },
        func="async_toggle_schedule",
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_START_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_STOP_SESSION)
    hass.services.async_remove(DOMAIN, SERVICE_SET_INTENSITY)
    hass.services.async_remove(DOMAIN, SERVICE_SET_FRAGRANCE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_ROOM_NAME)
    hass.services.async_remove(DOMAIN, SERVICE_GET_SCHEDULES)
    hass.services.async_remove(DOMAIN, SERVICE_REFRESH_SCHEDULES)
    hass.services.async_remove(DOMAIN, SERVICE_CREATE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_DELETE_SCHEDULE)
    hass.services.async_remove(DOMAIN, SERVICE_TOGGLE_SCHEDULE)
