"""
Aera Device API - High-level interface for Aera Smart Diffusers.

Provides a simple interface to control Aera diffusers:
- Power on/off
- Set intensity (1-10)
- Start/stop sessions with timers
- Get device status
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum
import logging

from .client import AylaApi, AylaApiError

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
    
    def __init__(self, api: AylaApi, dsn: str, device_info: dict = None):
        """
        Initialize an Aera device.
        
        Args:
            api: Authenticated AylaApi instance
            dsn: Device Serial Number
            device_info: Optional device info dict from API
        """
        self._api = api
        self._dsn = dsn
        self._device_info = device_info or {}
        self._state: Optional[AeraDeviceState] = None
        self._properties: dict = {}
    
    @property
    def dsn(self) -> str:
        """Device Serial Number."""
        return self._dsn
    
    @property
    def name(self) -> str:
        """Device name."""
        return self._device_info.get("product_name", self._dsn)
    
    @property
    def model(self) -> str:
        """Device model."""
        return self._device_info.get("oem_model", "Unknown")
    
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
        # Get device info if not already cached
        if not self._device_info:
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
            List of AeraDevice objects
        """
        raw_devices = await self._ayla_api.get_devices()
        
        self._devices = []
        for raw in raw_devices:
            device = AeraDevice(
                api=self._ayla_api,
                dsn=raw.dsn,
                device_info={
                    "product_name": raw.product_name,
                    "model": raw.model,
                    "oem_model": raw.device_type,
                    "connection_status": raw.connection_status,
                }
            )
            self._devices.append(device)
        
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
    
    async def close(self):
        """Close the API connection."""
        await self._ayla_api.close()
