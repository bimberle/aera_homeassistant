"""Fan platform for Aera."""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN, INTENSITY_MAX, INTENSITY_MIN
from .coordinator import AeraCoordinator
from .entity import AeraEntity

if TYPE_CHECKING:
    from .ayla_api import AeraDevice

_LOGGER = logging.getLogger(__name__)

INTENSITY_RANGE = (INTENSITY_MIN, INTENSITY_MAX)


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


class AeraFan(AeraEntity, FanEntity):
    """Representation of an Aera diffuser as a fan."""

    _attr_name = None  # Use device name
    _attr_supported_features = FanEntityFeature.SET_SPEED
    _attr_speed_count = INTENSITY_MAX - INTENSITY_MIN + 1

    def __init__(
        self,
        coordinator: AeraCoordinator,
        device: "AeraDevice",
    ) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{device.dsn}_fan"

    @property
    def is_on(self) -> bool | None:
        """Return true if the diffuser is on."""
        if self.device.state is None:
            return None
        return self.device.state.is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        if self.device.state is None or not self.device.state.is_on:
            return 0
        return ranged_value_to_percentage(
            INTENSITY_RANGE, self.device.state.intensity
        )

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the diffuser."""
        if percentage is not None:
            intensity = math.ceil(
                percentage_to_ranged_value(INTENSITY_RANGE, percentage)
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
            percentage_to_ranged_value(INTENSITY_RANGE, percentage)
        )
        await self.device.set_intensity(intensity)
        
        if not self.is_on:
            await self.device.turn_on()
        
        await self.coordinator.async_request_refresh()
