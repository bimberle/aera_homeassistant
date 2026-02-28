"""
Aera Device API - High-level interface for Aera Smart Diffusers.

Provides a simple interface to control Aera diffusers:
- Power on/off
- Set intensity (1-10)
- Start/stop sessions with timers
- Get device status
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import IntEnum
import logging

from .client import AylaApi, AylaApiError, AylaSchedule, AylaScheduleAction

_LOGGER = logging.getLogger(__name__)


class AeraIntensity(IntEnum):
    """Intensity levels for Aera diffusers."""
    OFF = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6
    LEVEL_7 = 7
    LEVEL_8 = 8
    LEVEL_9 = 9
    LEVEL_10 = 10


class AeraMode(IntEnum):
    """Operating modes for Aera diffusers."""
    MANUAL = 0
    SCHEDULED = 1


class AeraSessionDuration(IntEnum):
    """Standard session durations in minutes."""
    HOURS_2 = 120   # 2 hours
    HOURS_4 = 240   # 4 hours
    HOURS_8 = 480   # 8 hours


@dataclass
class AeraDeviceState:
    """Current state of an Aera device."""
    # Device info
    dsn: str
    name: str
    model: str
    oem_model: str
    is_online: bool
    firmware_version: str
    
    # Power state
    power_on: bool
    
    # Intensity
    intensity: int
    intensity_manual: int
    intensity_scheduled: Optional[int]
    
    # Mode
    mode: AeraMode
    
    # Session
    session_active: bool
    session_time_left: int  # seconds
    session_length: int = 0  # configured session length in minutes
    
    # Cartridge (only for aera31 and similar)
    cartridge_present: Optional[bool] = None
    cartridge_usage: Optional[int] = None  # percentage used (0-100)
    fragrance_name: Optional[str] = None
    
    # aeraMini specific
    pump_life_time: Optional[int] = None  # pump lifetime counter
    
    @property
    def fill_level(self) -> Optional[int]:
        """Remaining fill level in percent (0-100). Only available for aera31."""
        if self.cartridge_usage is not None:
            return 100 - self.cartridge_usage
        return None
    
    # Raw properties for debugging
    raw_properties: dict = field(default_factory=dict)


class AeraDevice:
    """High-level interface for an Aera diffuser device."""
    
    def __init__(self, api: AylaApi, dsn: str, key: int = 0, device_info: dict = None):
        """
        Initialize an Aera device.
        
        Args:
            api: Authenticated AylaApi instance
            dsn: Device Serial Number
            key: Ayla device key (numeric ID for schedule API)
            device_info: Optional device info dict from API
        """
        self._api = api
        self._dsn = dsn
        self._key = key
        self._device_info = device_info or {}
        self._state: Optional[AeraDeviceState] = None
        self._properties: dict = {}
        self._room_name: str = ""
        self._ordered_position: int = 0
    
    @property
    def dsn(self) -> str:
        """Device Serial Number."""
        return self._dsn
    
    @property
    def key(self) -> int:
        """Ayla device key (numeric ID for schedule API)."""
        return self._key
    
    @property
    def name(self) -> str:
        """Device name (room name if set, otherwise DSN)."""
        if self._room_name:
            return self._room_name
        return self._device_info.get("product_name", self._dsn)
    
    @property
    def room_name(self) -> str:
        """Room name for the device."""
        return self._room_name
    
    @room_name.setter
    def room_name(self, value: str) -> None:
        """Set room name."""
        self._room_name = value
    
    @property
    def ordered_position(self) -> int:
        """Display order position."""
        return self._ordered_position
    
    @ordered_position.setter
    def ordered_position(self, value: int) -> None:
        """Set ordered position."""
        self._ordered_position = value
    
    @property
    def model(self) -> str:
        """Device model."""
        return self._device_info.get("oem_model", "Unknown")
    
    @property
    def connection_status(self) -> str:
        """Connection status (Online/Offline)."""
        return self._device_info.get("connection_status", "Unknown")
    
    @property
    def is_online(self) -> bool:
        """Check if device is online."""
        return self.connection_status == "Online"
    
    @property
    def state(self) -> Optional[AeraDeviceState]:
        """Current device state (call update() first)."""
        return self._state
    
    async def update(self) -> AeraDeviceState:
        """
        Fetch the latest state from the device.
        
        Returns:
            AeraDeviceState with current values
        """
        # Always refresh device info to get latest connection_status
        devices = await self._api.get_devices()
        for d in devices:
            if d.dsn == self._dsn:
                self._device_info = {
                    "product_name": d.product_name,
                    "model": d.model,
                    "oem_model": d.device_type,
                    "connection_status": d.connection_status,
                }
                break
        
        # Get properties
        self._properties = await self._api.get_device_properties(self._dsn)
        
        # Parse properties into state
        self._state = self._parse_state()
        return self._state
    
    def _get_prop_value(self, name: str, default=None):
        """Get a property value safely."""
        prop = self._properties.get(name, {})
        value = prop.get("value") if isinstance(prop, dict) else prop
        return value if value is not None else default
    
    def _parse_state(self) -> AeraDeviceState:
        """Parse raw properties into AeraDeviceState."""
        return AeraDeviceState(
            dsn=self._dsn,
            name=self._device_info.get("product_name", self._dsn),
            model=self._device_info.get("model", ""),
            oem_model=self._device_info.get("oem_model", ""),
            is_online=self._device_info.get("connection_status") == "Online",
            firmware_version=self._get_prop_value("device_fw_version", ""),
            
            power_on=self._get_prop_value("power_state", 0) == 1,
            
            intensity=self._get_prop_value("intensity_state", 0),
            intensity_manual=self._get_prop_value("set_intensity_manual", 5),
            intensity_scheduled=self._get_prop_value("set_intensity_sched"),
            
            mode=AeraMode(self._get_prop_value("mode_state", 0)),
            
            session_active=self._get_prop_value("session_state", 0) == 1,
            session_time_left=self._get_prop_value("session_time_left", 0),
            session_length=self._get_prop_value("set_session_length", 0),
            
            cartridge_present=self._get_prop_value("cartridge_present") == 1 
                if self._get_prop_value("cartridge_present") is not None else None,
            cartridge_usage=self._get_prop_value("cartridge_usage"),
            fragrance_name=self._get_prop_value("fragrance_name"),
            
            pump_life_time=self._get_prop_value("pump_life_time"),
            
            raw_properties=self._properties,
        )
    
    async def turn_on(self) -> bool:
        """Turn the diffuser on."""
        _LOGGER.info(f"Turning on device {self._dsn}")
        result = await self._api.set_property(self._dsn, "set_power_state", 1)
        if result:
            await self.update()
        return result
    
    async def turn_off(self) -> bool:
        """Turn the diffuser off."""
        _LOGGER.info(f"Turning off device {self._dsn}")
        result = await self._api.set_property(self._dsn, "set_power_state", 0)
        if result:
            await self.update()
        return result
    
    async def set_intensity(self, level: int) -> bool:
        """
        Set the fragrance intensity level.
        
        Args:
            level: Intensity level 1-10
            
        Returns:
            True if successful
        """
        if not 1 <= level <= 10:
            raise ValueError("Intensity must be between 1 and 10")
        
        _LOGGER.info(f"Setting intensity to {level} for device {self._dsn}")
        result = await self._api.set_property(self._dsn, "set_intensity_manual", level)
        if result:
            await self.update()
        return result
    
    async def start_session(self, duration_minutes: int = 240) -> bool:
        """
        Start a timed session.
        
        Standard durations:
        - 120 minutes (2 hours)
        - 240 minutes (4 hours)  [default]
        - 480 minutes (8 hours)
        
        Args:
            duration_minutes: Session duration in minutes
            
        Returns:
            True if successful
        """
        _LOGGER.info(f"Starting {duration_minutes}min session for device {self._dsn}")
        # Must turn off first, then set session length, then turn on
        await self._api.set_property(self._dsn, "set_power_state", 0)
        await self._api.set_property(self._dsn, "set_session_length", duration_minutes)
        result = await self._api.set_property(self._dsn, "set_power_state", 1)
        if result:
            await self.update()
        return result
    
    async def stop_session(self) -> bool:
        """
        Stop the active session.
        
        This sets session_length to 0 and turns off the device.
        
        Returns:
            True if successful
        """
        _LOGGER.info(f"Stopping session for device {self._dsn}")
        # Set session length to 0 to stop the session timer
        await self._api.set_property(self._dsn, "set_session_length", 0)
        # Turn off the device
        result = await self._api.set_property(self._dsn, "set_power_state", 0)
        if result:
            await self.update()
        return result
    
    async def set_fragrance(self, fragrance_id: str) -> bool:
        """
        Set the fragrance identifier (aeraMini only).
        
        The fragrance ID is a 3-letter code, e.g.:
        - "IDG" for Indigo
        - "LVR" for Lavender
        - "OBZ" for Ocean Breeze
        
        See fragrances.py for the full list of known fragrance IDs.
        
        Note: This is only available on aeraMini devices.
        The aera31 automatically detects the fragrance from the cartridge.
        
        Args:
            fragrance_id: 3-letter fragrance code (e.g., "IDG", "LVR")
            
        Returns:
            True if successful
        """
        _LOGGER.info(f"Setting fragrance to {fragrance_id} for device {self._dsn}")
        result = await self._api.set_property(self._dsn, "set_fragrance_identifier", fragrance_id.upper())
        if result:
            await self.update()
        return result

    async def set_room_name(self, room_name: str) -> bool:
        """
        Set the room name for this device.
        
        Args:
            room_name: The room name to set
            
        Returns:
            True if successful
        """
        _LOGGER.info(f"Setting room name to '{room_name}' for device {self._dsn}")
        result = await self._api.set_device_metadata(
            self._dsn, 
            room_name, 
            self._ordered_position
        )
        if result:
            self._room_name = room_name
        return result

    # =========================================================================
    # Schedule Management
    # =========================================================================

    async def get_schedules(self) -> List[AylaSchedule]:
        """
        Get all schedules for this device.
        
        Returns:
            List of AylaSchedule objects with their actions.
        """
        _LOGGER.info(f"Getting schedules for device {self._dsn} (key={self._key})")
        return await self._api.get_schedules(self._key)
    
    async def create_schedule(
        self,
        name: str,
        start_time: str = "08:00",
        end_time: str = "22:00",
        days: List[int] = None,
        intensity: int = 5,
        power_on: bool = True,
        active: bool = True,
    ) -> AylaSchedule:
        """
        Create a new schedule for this device.
        
        Args:
            name: Display name for the schedule
            start_time: Start time in HH:MM format (24h)
            end_time: End time in HH:MM format (24h)
            days: Days of week (1=Sunday, 2=Monday, ..., 7=Saturday)
                  Default is Monday-Friday [2,3,4,5,6]
            intensity: Intensity level 1-10
            power_on: Whether to turn on at start (True) or off (False)
            active: Whether the schedule is active
            
        Returns:
            Created AylaSchedule with server-assigned key.
        """
        if days is None:
            days = [2, 3, 4, 5, 6]  # Monday-Friday
        
        # Convert HH:MM to HH:MM:SS
        start_time_full = f"{start_time}:00" if len(start_time) == 5 else start_time
        end_time_full = f"{end_time}:00" if len(end_time) == 5 else end_time
        
        # Create unique name for API
        import time
        unique_name = f"aera_schedule_{int(time.time())}"
        
        schedule = AylaSchedule(
            name=unique_name,
            display_name=name,
            active=active,
            start_time_each_day=start_time_full,
            end_time_each_day=end_time_full,
            days_of_week=days,
            actions=[
                # Power on action at start
                AylaScheduleAction(
                    name="set_power_state",
                    base_type="integer",
                    value="1" if power_on else "0",
                    at_start=True,
                    at_end=False,
                ),
                # Set intensity at start
                AylaScheduleAction(
                    name="set_intensity_manual",
                    base_type="integer",
                    value=str(intensity),
                    at_start=True,
                    at_end=False,
                ),
                # Power off action at end
                AylaScheduleAction(
                    name="set_power_state",
                    base_type="integer",
                    value="0",
                    at_start=False,
                    at_end=True,
                ),
            ]
        )
        
        _LOGGER.info(f"Creating schedule '{name}' for device {self._dsn} (key={self._key})")
        return await self._api.create_schedule(self._key, schedule)
    
    async def update_schedule(
        self,
        schedule_key: int,
        name: str = None,
        start_time: str = None,
        end_time: str = None,
        days: List[int] = None,
        intensity: int = None,
        active: bool = None,
    ) -> AylaSchedule:
        """
        Update an existing schedule.
        
        Args:
            schedule_key: The schedule key to update
            name: New display name (optional)
            start_time: New start time in HH:MM format (optional)
            end_time: New end time in HH:MM format (optional)
            days: New days of week (optional)
            intensity: New intensity level (optional)
            active: New active state (optional)
            
        Returns:
            Updated AylaSchedule.
        """
        # First fetch the existing schedule
        schedules = await self.get_schedules()
        schedule = None
        for s in schedules:
            if s.key == schedule_key:
                schedule = s
                break
        
        if not schedule:
            raise AylaApiError(f"Schedule {schedule_key} not found")
        
        # Update fields
        if name is not None:
            schedule.display_name = name
        if start_time is not None:
            schedule.start_time_each_day = f"{start_time}:00" if len(start_time) == 5 else start_time
        if end_time is not None:
            schedule.end_time_each_day = f"{end_time}:00" if len(end_time) == 5 else end_time
        if days is not None:
            schedule.days_of_week = days
        if active is not None:
            schedule.active = active
        
        # Update the schedule itself
        updated = await self._api.update_schedule(schedule)
        
        # Update intensity action if specified
        if intensity is not None:
            for action in schedule.actions:
                if action.name == "set_intensity_manual" and action.key:
                    action.value = str(intensity)
                    await self._api.update_schedule_action(action)
                    break
        
        _LOGGER.info(f"Updated schedule {schedule_key} for device {self._dsn}")
        return updated
    
    async def delete_schedule(self, schedule_key: int) -> bool:
        """
        Delete a schedule.
        
        Args:
            schedule_key: The schedule key to delete
            
        Returns:
            True if successful.
        """
        _LOGGER.info(f"Deleting schedule {schedule_key} for device {self._dsn}")
        return await self._api.delete_schedule(schedule_key)
    
    async def toggle_schedule(self, schedule_key: int, active: bool) -> AylaSchedule:
        """
        Enable or disable a schedule.
        
        Args:
            schedule_key: The schedule key to toggle
            active: True to enable, False to disable
            
        Returns:
            Updated AylaSchedule.
        """
        return await self.update_schedule(schedule_key, active=active)


class AeraApi:
    """
    High-level API for Aera Smart Diffusers.
    
    Example usage:
        api = AeraApi("email@example.com", "password")
        await api.login()
        
        devices = await api.get_devices()
        for device in devices:
            state = await device.update()
            print(f"{state.name}: Power={'ON' if state.power_on else 'OFF'}")
            
            await device.turn_on()
            await device.set_intensity(5)
    """
    
    def __init__(self, email: str, password: str):
        """
        Initialize the Aera API.
        
        Args:
            email: Aera account email
            password: Aera account password
        """
        self._ayla_api = AylaApi(email, password)
        self._devices: list[AeraDevice] = []
    
    async def login(self) -> bool:
        """
        Login to the Aera/Ayla cloud.
        
        Returns:
            True if login successful
        """
        await self._ayla_api.login()
        return True
    
    async def get_devices(self) -> list[AeraDevice]:
        """
        Get all Aera devices on the account.
        
        Returns:
            List of AeraDevice objects (sorted by ordered_position)
        """
        raw_devices = await self._ayla_api.get_devices(include_metadata=True)
        
        self._devices = []
        for raw in raw_devices:
            device = AeraDevice(
                api=self._ayla_api,
                dsn=raw.dsn,
                key=raw.key,  # Numeric device key for schedule API
                device_info={
                    "product_name": raw.product_name,
                    "model": raw.model,
                    "oem_model": raw.device_type,
                    "connection_status": raw.connection_status,
                }
            )
            # Set room name and position from metadata
            device.room_name = raw.room_name
            device.ordered_position = raw.ordered_position
            self._devices.append(device)
        
        # Sort by ordered_position
        self._devices.sort(key=lambda d: d.ordered_position)
        
        return self._devices
    
    async def get_device(self, dsn: str) -> Optional[AeraDevice]:
        """
        Get a specific device by DSN.
        
        Args:
            dsn: Device Serial Number
            
        Returns:
            AeraDevice or None if not found
        """
        if not self._devices:
            await self.get_devices()
        
        for device in self._devices:
            if device.dsn == dsn:
                return device
        return None
    
    async def set_room_name(self, dsn: str, room_name: str) -> bool:
        """
        Set the room name for a device.
        
        Args:
            dsn: Device Serial Number
            room_name: The room name to set
            
        Returns:
            True if successful
        """
        device = await self.get_device(dsn)
        if device:
            return await device.set_room_name(room_name)
        return False
    
    async def close(self):
        """Close the API connection."""
        await self._ayla_api.close()
