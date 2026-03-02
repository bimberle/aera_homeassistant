"""Services for Aera integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.fan import DOMAIN as FAN_DOMAIN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, service

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Aera integration."""
    _LOGGER.debug("=== AERA async_setup_services called ===")
    _LOGGER.info("Aera: Setting up services for domain '%s'", DOMAIN)

    # Check if services.yaml exists
    import os
    services_yaml_path = os.path.join(os.path.dirname(__file__), "services.yaml")
    _LOGGER.debug("Aera: Looking for services.yaml at: %s", services_yaml_path)
    _LOGGER.debug("Aera: services.yaml exists: %s", os.path.exists(services_yaml_path))

    _LOGGER.debug("Aera: Registering start_session service")
    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "start_session",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("duration"): vol.In(["2h", "4h", "8h"]),
        },
        func="async_start_session",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "stop_session",
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_stop_session",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_intensity",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("intensity"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            ),
        },
        func="async_set_intensity_service",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_fragrance",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("fragrance_id"): cv.string,
        },
        func="async_set_fragrance",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "set_room_name",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("room_name"): cv.string,
        },
        func="async_set_room_name",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "refresh_schedules",
        entity_domain=FAN_DOMAIN,
        schema=None,
        func="async_refresh_schedules",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "create_schedule",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("schedule_name"): cv.string,
            vol.Optional("start_time", default="08:00"): cv.string,
            vol.Optional("end_time", default="22:00"): cv.string,
            vol.Optional("days", default=[2, 3, 4, 5, 6]): vol.All(
                cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]
            ),
            vol.Optional("intensity", default=5): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            ),
            vol.Optional("active", default=True): cv.boolean,
        },
        func="async_create_schedule",
    )

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
            vol.Optional("days"): vol.All(
                cv.ensure_list, [vol.In([1, 2, 3, 4, 5, 6, 7])]
            ),
            vol.Optional("intensity"): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            ),
            vol.Optional("active"): cv.boolean,
        },
        func="async_update_schedule",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "delete_schedule",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("schedule_key"): vol.Coerce(int),
        },
        func="async_delete_schedule",
    )

    service.async_register_platform_entity_service(
        hass,
        DOMAIN,
        "toggle_schedule",
        entity_domain=FAN_DOMAIN,
        schema={
            vol.Required("schedule_key"): vol.Coerce(int),
            vol.Required("active"): cv.boolean,
        },
        func="async_toggle_schedule",
    )
