"""Fan platform for Aera."""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN, INTENSITY_MIN
from .coordinator import AeraCoordinator
from .entity import AeraEntity

if TYPE_CHECKING:
    from .ayla_api import AeraDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aera fan entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        AeraFan(coordinator, device)
        for device in coordinator.devices.values()
    )

    # Register entity services
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        "start_session",
        {vol.Required("duration"): vol.In(["2h", "4h", "8h"])},
        "async_start_session",
    )

    platform.async_register_entity_service(
        "stop_session",
        None,
        "async_stop_session",
    )

    platform.async_register_entity_service(
        "set_intensity",
        {vol.Required("intensity"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10))},
        "async_set_intensity_service",
    )

    platform.async_register_entity_service(
        "set_fragrance",
        {vol.Required("fragrance_id"): cv.string},
        "async_set_fragrance",
    )

    platform.async_register_entity_service(
        "set_room_name",
        {vol.Required("room_name"): cv.string},
        "async_set_room_name",
    )

    platform.async_register_entity_service(
        "refresh_schedules",
        None,
        "async_refresh_schedules",
    )

    platform.async_register_entity_service(
        "create_schedule",
        {
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
        "async_create_schedule",
    )

    platform.async_register_entity_service(
        "update_schedule",
        {
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
        "async_update_schedule",
    )

    platform.async_register_entity_service(
        "delete_schedule",
        {vol.Required("schedule_key"): vol.Coerce(int)},
        "async_delete_schedule",
    )

    platform.async_register_entity_service(
        "toggle_schedule",
        {
            vol.Required("schedule_key"): vol.Coerce(int),
            vol.Required("active"): cv.boolean,
        },
        "async_toggle_schedule",
    )


class AeraFan(AeraEntity, FanEntity):
    """Representation of an Aera diffuser as a fan."""

    _attr_name = None  # Use device name
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED 
        | FanEntityFeature.TURN_ON 
        | FanEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: AeraCoordinator,
        device: "AeraDevice",
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{device.dsn}_fan"

    @property
    def _intensity_range(self) -> tuple[int, int]:
        """Return the intensity range for this device."""
        return (INTENSITY_MIN, self.device.max_intensity)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds supported."""
        return self.device.max_intensity - INTENSITY_MIN + 1

    @property
    def is_on(self) -> bool | None:
        """Return true if the diffuser is on."""
        if self.device.state is None:
            return None
        return self.device.state.power_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        if self.device.state is None or not self.device.state.power_on:
            return 0
        return ranged_value_to_percentage(
            self._intensity_range, self.device.state.intensity
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device.is_online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        # Determine device type based on max_intensity
        device_type = "aeraMini" if self.device.max_intensity == 5 else "aera31"
        
        attrs = {
            "room_name": self.device.room_name,
            "dsn": self.device.dsn,
            "connection_status": self.device.connection_status,
            "max_intensity": self.device.max_intensity,
            "device_type": device_type,
            "model": self.device.model,
        }
        if self.device.state:
            attrs["session_active"] = self.device.state.session_active
            attrs["session_time_remaining"] = self.device.state.session_time_left
            attrs["intensity"] = self.device.state.intensity
            attrs["firmware_version"] = self.device.state.firmware_version
            # Mode: 0 = Manual, 1 = Scheduled
            attrs["mode"] = "scheduled" if self.device.state.mode == 1 else "manual"
            if self.device.state.fragrance_name:
                attrs["fragrance"] = self.device.state.fragrance_name
            if self.device.state.fill_level is not None:
                attrs["fill_level"] = self.device.state.fill_level
            # aeraMini specific
            if self.device.state.pump_life_time is not None:
                attrs["pump_life_time"] = self.device.state.pump_life_time
        
        # Add schedules
        if self.device.schedules:
            attrs["schedules"] = []
            for s in self.device.schedules:
                # Extract intensity from actions
                intensity = None
                for a in s.actions:
                    if a.name in ("set_intensity_sched", "set_intensity_manual"):
                        try:
                            intensity = int(a.value)
                        except (ValueError, TypeError):
                            pass
                        break
                
                attrs["schedules"].append({
                    "key": s.key,
                    "name": s.display_name,
                    "active": s.active,
                    "start_time": s.start_time_each_day[:5],  # HH:MM
                    "end_time": s.end_time_each_day[:5],      # HH:MM
                    "days": s.days_of_week,
                    "intensity": intensity,
                    "actions": [{"name": a.name, "value": a.value} for a in s.actions],
                })
        else:
            attrs["schedules"] = []
        
        return attrs

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the diffuser."""
        if percentage is not None:
            intensity = math.ceil(
                percentage_to_ranged_value(self._intensity_range, percentage)
            )
            await self.device.set_intensity(intensity)
        await self.device.turn_on()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the diffuser."""
        await self.device.turn_off()
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return

        intensity = math.ceil(
            percentage_to_ranged_value(self._intensity_range, percentage)
        )
        await self.device.set_intensity(intensity)
        
        if not self.is_on:
            await self.device.turn_on()
        
        await self.coordinator.async_request_refresh()

    # Service methods for entity services
    async def async_start_session(self, duration: str) -> None:
        """Start a fragrance session."""
        from .const import SESSION_DURATIONS
        duration_minutes = SESSION_DURATIONS.get(duration)
        if duration_minutes is None:
            _LOGGER.error("Invalid duration: %s", duration)
            return
        await self.device.start_session(duration_minutes)
        _LOGGER.info("Started %s session on %s", duration, self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_stop_session(self) -> None:
        """Stop the current session."""
        await self.device.stop_session()
        _LOGGER.info("Stopped session on %s", self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_set_intensity_service(self, intensity: int) -> None:
        """Set the fragrance intensity via service."""
        await self.device.set_intensity(intensity)
        _LOGGER.info("Set intensity to %d on %s", intensity, self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_set_fragrance(self, fragrance_id: str) -> None:
        """Set fragrance on device."""
        await self.device.set_fragrance(fragrance_id)
        _LOGGER.info("Set fragrance %s on %s", fragrance_id, self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_set_room_name(self, room_name: str) -> None:
        """Set room name on device."""
        await self.device.set_room_name(room_name)
        _LOGGER.info("Set room name '%s' on %s", room_name, self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_get_schedules(self) -> dict:
        """Get all schedules for the device."""
        schedules = await self.device.get_schedules()
        result = [
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
        _LOGGER.info("Got %d schedules for %s", len(schedules), self.device.name)
        return {"schedules": result}

    async def async_refresh_schedules(self) -> None:
        """Invalidate schedule cache and reload schedules."""
        _LOGGER.info("Refreshing schedules for %s", self.device.name)
        self.device.invalidate_schedule_cache()
        await self.coordinator.async_request_refresh()

    async def async_create_schedule(
        self,
        schedule_name: str,
        start_time: str = "08:00",
        end_time: str = "22:00",
        days: list[int] | None = None,
        intensity: int = 5,
        active: bool = True,
    ) -> dict:
        """Create a new schedule."""
        if days is None:
            days = [2, 3, 4, 5, 6]  # Mon-Fri
        schedule = await self.device.create_schedule(
            name=schedule_name,
            start_time=start_time,
            end_time=end_time,
            days=days,
            intensity=intensity,
            active=active,
        )
        _LOGGER.info("Created schedule '%s' on %s", schedule_name, self.device.name)
        await self.coordinator.async_request_refresh()
        return {"key": schedule.key, "name": schedule.display_name}

    async def async_update_schedule(
        self,
        schedule_key: int,
        schedule_name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        days: list[int] | None = None,
        intensity: int | None = None,
        active: bool | None = None,
    ) -> dict:
        """Update an existing schedule."""
        _LOGGER.debug(
            "async_update_schedule called: schedule_key=%s (type=%s), start_time=%s, end_time=%s, days=%s, intensity=%s",
            schedule_key, type(schedule_key).__name__, start_time, end_time, days, intensity
        )
        schedule = await self.device.update_schedule(
            schedule_key=schedule_key,
            name=schedule_name,
            start_time=start_time,
            end_time=end_time,
            days=days,
            intensity=intensity,
            active=active,
        )
        _LOGGER.info("Updated schedule %d on %s", schedule_key, self.device.name)
        await self.coordinator.async_request_refresh()
        return {"key": schedule.key, "name": schedule.display_name}

    async def async_delete_schedule(self, schedule_key: int) -> None:
        """Delete a schedule."""
        await self.device.delete_schedule(schedule_key)
        _LOGGER.info("Deleted schedule %d on %s", schedule_key, self.device.name)
        await self.coordinator.async_request_refresh()

    async def async_toggle_schedule(self, schedule_key: int, active: bool) -> dict:
        """Enable or disable a schedule."""
        schedule = await self.device.toggle_schedule(schedule_key, active)
        _LOGGER.info("Toggled schedule %d to %s on %s", schedule_key, active, self.device.name)
        await self.coordinator.async_request_refresh()
        return {"key": schedule.key, "active": schedule.active}
