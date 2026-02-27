"""Sensor platform for Aera."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import AeraCoordinator
from .entity import AeraEntity

if TYPE_CHECKING:
    from .ayla_api import AeraDevice, AeraDeviceState


@dataclass(frozen=True, kw_only=True)
class AeraSensorEntityDescription(SensorEntityDescription):
    """Describes Aera sensor entity."""

    value_fn: Callable[["AeraDeviceState"], int | str | None]
    available_fn: Callable[["AeraDevice"], bool] = lambda _: True


SENSOR_DESCRIPTIONS: tuple[AeraSensorEntityDescription, ...] = (
    AeraSensorEntityDescription(
        key="intensity",
        translation_key="intensity",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.intensity,
    ),
    AeraSensorEntityDescription(
        key="fill_level",
        translation_key="fill_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.fill_level,
        available_fn=lambda device: device.state is not None and device.state.fill_level is not None,
    ),
    AeraSensorEntityDescription(
        key="session_time_remaining",
        translation_key="session_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.session_time_left,
    ),
    AeraSensorEntityDescription(
        key="fragrance",
        translation_key="fragrance",
        value_fn=lambda state: state.fragrance_name,
    ),
    AeraSensorEntityDescription(
        key="pump_lifetime",
        translation_key="pump_lifetime",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda state: state.pump_life_time,
        available_fn=lambda device: device.state is not None and device.state.pump_life_time is not None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aera sensor entities."""
    coordinator: AeraCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[AeraSensor] = []
    for device in coordinator.devices.values():
        for description in SENSOR_DESCRIPTIONS:
            if description.available_fn(device):
                entities.append(AeraSensor(coordinator, device, description))

    async_add_entities(entities)


class AeraSensor(AeraEntity, SensorEntity):
    """Representation of an Aera sensor."""

    entity_description: AeraSensorEntityDescription

    def __init__(
        self,
        coordinator: AeraCoordinator,
        device: "AeraDevice",
        description: AeraSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device)
        self.entity_description = description
        self._attr_unique_id = f"{device.dsn}_{description.key}"

    @property
    def native_value(self) -> int | str | None:
        """Return the sensor value."""
        if self.device.state is None:
            return None
        return self.entity_description.value_fn(self.device.state)
