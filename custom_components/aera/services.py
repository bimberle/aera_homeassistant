"""Services for Aera integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, service
from homeassistant.helpers.service import async_set_service_schema

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Aera integration."""
    _LOGGER.debug("=== AERA async_setup_services called ===")
    _LOGGER.info("Aera: Setting up services for domain '%s'", DOMAIN)

    # start_session
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "start_session",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("duration"): vol.In(["2h", "4h", "8h"])},
        func="async_start_session",
    )
    async_set_service_schema(hass, DOMAIN, "start_session", {
        "name": "Start Session",
        "description": "Start a timed fragrance session.",
        "fields": {
            "duration": {
                "name": "Duration",
                "description": "Session duration",
                "required": True,
                "selector": {
                    "select": {
                        "options": [
                            {"label": "2 hours", "value": "2h"},
                            {"label": "4 hours", "value": "4h"},
                            {"label": "8 hours", "value": "8h"},
                        ]
                    }
                }
            }
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # stop_session
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "stop_session",
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_stop_session",
    )
    async_set_service_schema(hass, DOMAIN, "stop_session", {
        "name": "Stop Session",
        "description": "Stop the current fragrance session.",
        "fields": {},
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # set_intensity
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_intensity",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("intensity"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10))},
        func="async_set_intensity_service",
    )
    async_set_service_schema(hass, DOMAIN, "set_intensity", {
        "name": "Set Intensity",
        "description": "Set the fragrance intensity level (1-10).",
        "fields": {
            "intensity": {
                "name": "Intensity",
                "description": "Intensity level from 1 (lowest) to 10 (highest)",
                "required": True,
                "selector": {"number": {"min": 1, "max": 10, "step": 1, "mode": "slider"}}
            }
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # set_fragrance
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_fragrance",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("fragrance_id"): cv.string},
        func="async_set_fragrance",
    )
    async_set_service_schema(hass, DOMAIN, "set_fragrance", {
        "name": "Set Fragrance",
        "description": "Set the fragrance for aeraMini devices.",
        "fields": {
            "fragrance_id": {
                "name": "Fragrance ID",
                "description": "The 3-letter fragrance identifier (e.g., 'IDG' for Indigo)",
                "required": True,
                "example": "IDG",
                "selector": {"text": {}}
            }
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # set_room_name
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_room_name",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("room_name"): cv.string},
        func="async_set_room_name",
    )
    async_set_service_schema(hass, DOMAIN, "set_room_name", {
        "name": "Set Room Name",
        "description": "Set the room name for an Aera device.",
        "fields": {
            "room_name": {
                "name": "Room Name",
                "description": "The name of the room where the device is located",
                "required": True,
                "example": "Living Room",
                "selector": {"text": {}}
            }
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # refresh_schedules
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "refresh_schedules",
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_refresh_schedules",
    )
    async_set_service_schema(hass, DOMAIN, "refresh_schedules", {
        "name": "Refresh Schedules",
        "description": "Force refresh of schedules from the cloud.",
        "fields": {},
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # create_schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "create_schedule",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("schedule_name"): cv.string,
            vol.Optional("start_time", default="08:00"): cv.string,
            vol.Optional("end_time", default="22:00"): cv.string,
            vol.Optional("days", default=[2, 3, 4, 5, 6]): vol.All(cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]),
            vol.Optional("intensity", default=5): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional("active", default=True): cv.boolean,
        },
        func="async_create_schedule",
    )
    async_set_service_schema(hass, DOMAIN, "create_schedule", {
        "name": "Create Schedule",
        "description": "Create a new fragrance schedule.",
        "fields": {
            "schedule_name": {"name": "Schedule Name", "description": "Name for the schedule", "required": True, "example": "Morning", "selector": {"text": {}}},
            "start_time": {"name": "Start Time", "description": "Start time (HH:MM)", "default": "08:00", "selector": {"time": {}}},
            "end_time": {"name": "End Time", "description": "End time (HH:MM)", "default": "22:00", "selector": {"time": {}}},
            "days": {"name": "Days", "description": "Days of the week (1=Sun, 2=Mon, ...)", "default": [2, 3, 4, 5, 6], "selector": {"select": {"multiple": True, "options": [{"label": "Sunday", "value": 1}, {"label": "Monday", "value": 2}, {"label": "Tuesday", "value": 3}, {"label": "Wednesday", "value": 4}, {"label": "Thursday", "value": 5}, {"label": "Friday", "value": 6}, {"label": "Saturday", "value": 7}]}}},
            "intensity": {"name": "Intensity", "description": "Intensity level (1-10)", "default": 5, "selector": {"number": {"min": 1, "max": 10}}},
            "active": {"name": "Active", "description": "Whether the schedule is active", "default": True, "selector": {"boolean": {}}}
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # update_schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "update_schedule",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("schedule_key"): vol.Coerce(int),
            vol.Optional("schedule_name"): cv.string,
            vol.Optional("start_time"): cv.string,
            vol.Optional("end_time"): cv.string,
            vol.Optional("days"): vol.All(cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]),
            vol.Optional("intensity"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional("active"): cv.boolean,
        },
        func="async_update_schedule",
    )
    async_set_service_schema(hass, DOMAIN, "update_schedule", {
        "name": "Update Schedule",
        "description": "Update an existing fragrance schedule.",
        "fields": {
            "schedule_key": {"name": "Schedule Key", "description": "The schedule key/ID to update", "required": True, "selector": {"number": {"mode": "box"}}},
            "schedule_name": {"name": "Schedule Name", "description": "New name for the schedule", "selector": {"text": {}}},
            "start_time": {"name": "Start Time", "description": "Start time (HH:MM)", "selector": {"time": {}}},
            "end_time": {"name": "End Time", "description": "End time (HH:MM)", "selector": {"time": {}}},
            "days": {"name": "Days", "description": "Days of the week", "selector": {"select": {"multiple": True, "options": [{"label": "Sunday", "value": 1}, {"label": "Monday", "value": 2}, {"label": "Tuesday", "value": 3}, {"label": "Wednesday", "value": 4}, {"label": "Thursday", "value": 5}, {"label": "Friday", "value": 6}, {"label": "Saturday", "value": 7}]}}},
            "intensity": {"name": "Intensity", "description": "Intensity level (1-10)", "selector": {"number": {"min": 1, "max": 10}}},
            "active": {"name": "Active", "description": "Whether the schedule is active", "selector": {"boolean": {}}}
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # delete_schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "delete_schedule",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("schedule_key"): vol.Coerce(int)},
        func="async_delete_schedule",
    )
    async_set_service_schema(hass, DOMAIN, "delete_schedule", {
        "name": "Delete Schedule",
        "description": "Delete a fragrance schedule.",
        "fields": {
            "schedule_key": {"name": "Schedule Key", "description": "The schedule key/ID to delete", "required": True, "selector": {"number": {"mode": "box"}}}
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    # toggle_schedule
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "toggle_schedule",
        entity_domain=FAN_DOMAIN,
        schema={vol.Required("schedule_key"): vol.Coerce(int), vol.Required("active"): cv.boolean},
        func="async_toggle_schedule",
    )
    async_set_service_schema(hass, DOMAIN, "toggle_schedule", {
        "name": "Toggle Schedule",
        "description": "Toggle a schedule on or off.",
        "fields": {
            "schedule_key": {"name": "Schedule Key", "description": "The schedule key/ID to toggle", "required": True, "selector": {"number": {"mode": "box"}}},
            "active": {"name": "Active", "description": "Whether the schedule should be active", "required": True, "selector": {"boolean": {}}}
        },
        "target": {"entity": {"integration": "aera", "domain": "fan"}}
    })

    _LOGGER.info("Aera: All services registered with schemas")
