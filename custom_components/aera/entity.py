"""Base entity for Aera."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AeraCoordinator

if TYPE_CHECKING:
    from .ayla_api import AeraDevice


class AeraEntity(CoordinatorEntity[AeraCoordinator]):
    """Base class for Aera entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AeraCoordinator,
        device: "AeraDevice",
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.dsn)},
            name=device.name,
            manufacturer="Aera",
            model=device.model,
            sw_version=device.state.firmware if device.state else None,
        )

    @property
    def device(self) -> "AeraDevice":
        """Return the device from coordinator data."""
        return self.coordinator.devices[self._device.dsn]
