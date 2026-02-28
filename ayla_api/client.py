"""
Ayla Networks API Client for Aera Smart Diffusers.

This module provides a Python interface to communicate with Aera devices
through the Ayla Networks IoT platform.
"""

import aiohttp
import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, List
import logging

_LOGGER = logging.getLogger(__name__)

# Ayla Networks Field (Production) endpoints
AYLA_USER_SERVICE = "https://user-field.aylanetworks.com"
AYLA_ADS_SERVICE = "https://ads-field.aylanetworks.com"
AYLA_RULES_SERVICE = "https://rulesservice-field.aylanetworks.com"

# Aera App Credentials (extracted from APK)
AERA_APP_ID = "android-id-id"
AERA_APP_SECRET = "android-id-oYOAkxPCU46_E04WxtwfOYatrUI"


@dataclass
class AylaAuthToken:
    """Authentication token data."""
    access_token: str
    refresh_token: str
    expires_in: int
    role: str
    role_tags: list


@dataclass
class DeviceMetadata:
    """Device metadata including room name and position."""
    dsn: str
    room_name: str
    ordered_position: int
    schedule_order: list


@dataclass
class AylaScheduleAction:
    """A single action within a schedule."""
    name: str                    # Property name to change
    base_type: str               # "integer", "boolean", etc.
    value: str                   # Value to set
    type: str = "property"       # "property" for property-based actions
    active: bool = True
    at_start: bool = True        # Execute at schedule start
    at_end: bool = False         # Execute at schedule end
    in_range: bool = False       # Execute while in range
    key: Optional[int] = None    # Server-assigned key (None for new actions)

    def to_dict(self) -> dict:
        """Convert to API format."""
        return {
            "name": self.name,
            "base_type": self.base_type,
            "value": self.value,
            "type": self.type,
            "active": self.active,
            "at_start": self.at_start,
            "at_end": self.at_end,
            "in_range": self.in_range,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AylaScheduleAction":
        """Create from API response."""
        return cls(
            name=data.get("name", ""),
            base_type=data.get("base_type", "integer"),
            value=str(data.get("value", "")),
            type=data.get("type", "property"),
            active=data.get("active", True),
            at_start=data.get("at_start", True),
            at_end=data.get("at_end", False),
            in_range=data.get("in_range", False),
            key=data.get("key"),
        )


@dataclass
class AylaSchedule:
    """Schedule for automating device actions."""
    name: str
    display_name: str
    active: bool = True
    start_time_each_day: str = "08:00:00"    # HH:MM:SS format
    end_time_each_day: str = "22:00:00"      # HH:MM:SS format
    days_of_week: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7])  # 1=Sunday, 7=Saturday
    utc: bool = False
    direction: str = "input"
    start_date: Optional[str] = None         # YYYY-MM-DD
    end_date: Optional[str] = None           # YYYY-MM-DD
    duration: int = 0
    interval: int = 0
    key: Optional[int] = None                # Server-assigned key
    actions: List[AylaScheduleAction] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to API format."""
        data = {
            "name": self.name,
            "display_name": self.display_name,
            "active": self.active,
            "start_time_each_day": self.start_time_each_day,
            "end_time_each_day": self.end_time_each_day,
            "days_of_week": self.days_of_week,
            "utc": self.utc,
            "direction": self.direction,
            "duration": self.duration,
            "interval": self.interval,
        }
        if self.start_date:
            data["start_date"] = self.start_date
        if self.end_date:
            data["end_date"] = self.end_date
        return data

    @classmethod
    def from_dict(cls, data: dict, actions: List[AylaScheduleAction] = None) -> "AylaSchedule":
        """Create from API response."""
        return cls(
            name=data.get("name", ""),
            display_name=data.get("display_name", data.get("name", "")),
            active=data.get("active", True),
            start_time_each_day=data.get("start_time_each_day", "08:00:00"),
            end_time_each_day=data.get("end_time_each_day", "22:00:00"),
            days_of_week=data.get("days_of_week", [1, 2, 3, 4, 5, 6, 7]),
            utc=data.get("utc", False),
            direction=data.get("direction", "input"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            duration=data.get("duration", 0),
            interval=data.get("interval", 0),
            key=data.get("key"),
            actions=actions or [],
        )


@dataclass
class AeraDevice:
    """Aera device representation."""
    dsn: str  # Device Serial Number
    key: int  # Ayla device key (numeric ID) - required for schedule API!
    product_name: str
    model: str
    device_type: str
    connection_status: str
    properties: dict
    room_name: str = ""  # Room name from metadata
    ordered_position: int = 0  # Display order
    
    @property
    def is_online(self) -> bool:
        return self.connection_status == "Online"


class AylaApiError(Exception):
    """Base exception for Ayla API errors."""
    pass


class AylaAuthError(AylaApiError):
    """Authentication error."""
    pass

class AylaApi:
    """Ayla Networks API Client."""
    
    def __init__(
        self,
        email: str,
        password: str,
        app_id: str = AERA_APP_ID,
        app_secret: str = AERA_APP_SECRET,
    ):
        self.email = email
        self.password = password
        self.app_id = app_id
        self.app_secret = app_secret
        self._auth_token: Optional[AylaAuthToken] = None
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_headers(self) -> dict:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._auth_token:
            headers["Authorization"] = f"auth_token {self._auth_token.access_token}"
        return headers
    
    async def login(self) -> AylaAuthToken:
        """
        Sign in to the Ayla IoT Cloud.
        
        Returns:
            AylaAuthToken with access and refresh tokens.
        """
        if not self.app_id or not self.app_secret:
            raise AylaApiError(
                "app_id and app_secret are required. "
                "Extract them from the Aera app traffic using mitmproxy."
            )
        
        session = await self._get_session()
        url = f"{AYLA_USER_SERVICE}/users/sign_in.json"
        
        payload = {
            "user": {
                "email": self.email,
                "password": self.password,
                "application": {
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                }
            }
        }
        
        _LOGGER.debug(f"Logging in to Ayla API as {self.email}")
        
        async with session.post(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status == 401:
                raise AylaAuthError("Invalid credentials")
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Login failed: {resp.status} - {text}")
            
            data = await resp.json()
            
        self._auth_token = AylaAuthToken(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data.get("expires_in", 86400),
            role=data.get("role", ""),
            role_tags=data.get("role_tags", []),
        )
        
        _LOGGER.info("Successfully logged in to Ayla API")
        return self._auth_token
    
    async def get_devices(self, include_metadata: bool = True) -> list[AeraDevice]:
        """
        Get all devices associated with the user account.
        
        Args:
            include_metadata: If True, also fetch room names from device metadata.
        
        Returns:
            List of AeraDevice objects.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/devices.json"
        
        _LOGGER.debug("Fetching devices from Ayla API")
        
        async with session.get(url, headers=self._get_headers()) as resp:
            if resp.status == 401:
                # Token might be expired, try to re-login
                await self.login()
                return await self.get_devices(include_metadata)
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get devices: {resp.status} - {text}")
            
            data = await resp.json()
        
        # Fetch metadata for room names
        metadata = {}
        if include_metadata:
            try:
                metadata = await self.get_device_metadata()
            except AylaApiError:
                _LOGGER.warning("Failed to fetch device metadata, continuing without room names")
        
        devices = []
        for item in data:
            device_data = item.get("device", {})
            dsn = device_data.get("dsn", "")
            device_key = device_data.get("key", 0)
            device_meta = metadata.get(dsn)
            
            _LOGGER.debug(f"Device {dsn}: key={device_key}")
            
            devices.append(AeraDevice(
                dsn=dsn,
                key=device_key,  # Numeric device key for schedule API
                product_name=device_data.get("product_name", ""),
                model=device_data.get("model", ""),
                device_type=device_data.get("device_type", ""),
                connection_status=device_data.get("connection_status", "Offline"),
                properties={},
                room_name=device_meta.room_name if device_meta else "",
                ordered_position=device_meta.ordered_position if device_meta else 0,
            ))
        
        # Sort by ordered_position if metadata was available
        if include_metadata and metadata:
            devices.sort(key=lambda d: d.ordered_position)
        
        _LOGGER.info(f"Found {len(devices)} devices")
        return devices
    
    async def get_device_properties(self, dsn: str) -> dict:
        """
        Get all properties for a specific device.
        
        Args:
            dsn: Device Serial Number
            
        Returns:
            Dictionary of property names to values.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/dsns/{dsn}/properties.json"
        
        _LOGGER.debug(f"Fetching properties for device {dsn}")
        
        async with session.get(url, headers=self._get_headers()) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get properties: {resp.status} - {text}")
            
            data = await resp.json()
        
        properties = {}
        for item in data:
            prop = item.get("property", {})
            properties[prop.get("name")] = {
                "value": prop.get("value"),
                "base_type": prop.get("base_type"),
                "read_only": prop.get("read_only", False),
                "direction": prop.get("direction"),
            }
        
        return properties
    
    async def set_property(self, dsn: str, property_name: str, value) -> bool:
        """
        Set a property value for a device.
        
        Args:
            dsn: Device Serial Number
            property_name: Name of the property to set
            value: New value for the property
            
        Returns:
            True if successful.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/dsns/{dsn}/properties/{property_name}/datapoints.json"
        
        payload = {
            "datapoint": {
                "value": value
            }
        }
        
        _LOGGER.debug(f"Setting {property_name}={value} for device {dsn}")
        
        async with session.post(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise AylaApiError(f"Failed to set property: {resp.status} - {text}")
        
        _LOGGER.info(f"Successfully set {property_name}={value} for device {dsn}")
        return True

    async def get_device_metadata(self) -> dict[str, DeviceMetadata]:
        """
        Get device metadata including room names from Ayla Datum API.
        
        Returns:
            Dict mapping DSN to DeviceMetadata objects.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_USER_SERVICE}/api/v1/users/data/device_data_table.json"
        
        _LOGGER.debug("Fetching device metadata from Ayla API")
        
        async with session.get(url, headers=self._get_headers()) as resp:
            if resp.status == 404:
                # No metadata exists yet
                return {}
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get device metadata: {resp.status} - {text}")
            
            data = await resp.json()
        
        result = {}
        try:
            value_str = data.get("datum", {}).get("value", "[]")
            metadata_list = json.loads(value_str)
            
            for item in metadata_list:
                dsn = item.get("dsn", "")
                if dsn:
                    result[dsn] = DeviceMetadata(
                        dsn=dsn,
                        room_name=item.get("room_name", ""),
                        ordered_position=item.get("ordered_position", 0),
                        schedule_order=item.get("schedule_order", []),
                    )
        except json.JSONDecodeError:
            _LOGGER.warning("Failed to parse device metadata JSON")
        
        return result
    
    async def set_device_metadata(
        self,
        dsn: str,
        room_name: Optional[str] = None,
        ordered_position: Optional[int] = None,
    ) -> bool:
        """
        Update device metadata (room name, position).
        
        Args:
            dsn: Device Serial Number
            room_name: New room name (optional)
            ordered_position: New display position (optional)
            
        Returns:
            True if successful.
        """
        if not self._auth_token:
            await self.login()
        
        # First fetch current metadata
        current_metadata = await self.get_device_metadata()
        
        # Build the updated metadata list
        metadata_list = []
        found = False
        
        for existing_dsn, meta in current_metadata.items():
            if existing_dsn == dsn:
                found = True
                metadata_list.append({
                    "dsn": dsn,
                    "room_name": room_name if room_name is not None else meta.room_name,
                    "ordered_position": ordered_position if ordered_position is not None else meta.ordered_position,
                    "schedule_order": meta.schedule_order,
                })
            else:
                metadata_list.append({
                    "dsn": existing_dsn,
                    "room_name": meta.room_name,
                    "ordered_position": meta.ordered_position,
                    "schedule_order": meta.schedule_order,
                })
        
        # If device not found in metadata, add it
        if not found:
            metadata_list.append({
                "dsn": dsn,
                "room_name": room_name or "",
                "ordered_position": ordered_position if ordered_position is not None else len(metadata_list),
                "schedule_order": [],
            })
        
        # Update the datum
        session = await self._get_session()
        url = f"{AYLA_USER_SERVICE}/api/v1/users/data/device_data_table.json"
        
        payload = {
            "datum": {
                "key": "device_data_table",
                "value": json.dumps(metadata_list),
            }
        }
        
        _LOGGER.debug(f"Updating device metadata for {dsn}")
        
        # Check if datum exists to decide between PUT and POST
        if current_metadata:
            # Update existing datum
            async with session.put(url, json=payload, headers=self._get_headers()) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise AylaApiError(f"Failed to update device metadata: {resp.status} - {text}")
        else:
            # Create new datum
            url = f"{AYLA_USER_SERVICE}/api/v1/users/data.json"
            async with session.post(url, json=payload, headers=self._get_headers()) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    raise AylaApiError(f"Failed to create device metadata: {resp.status} - {text}")
        
        _LOGGER.info(f"Successfully updated metadata for device {dsn}")
        return True

    # =========================================================================
    # Schedule API
    # =========================================================================
    
    async def get_schedules(self, device_key: int) -> List[AylaSchedule]:
        """
        Get all schedules for a device.
        
        Args:
            device_key: Ayla device key (numeric ID, NOT the DSN string!)
            
        Returns:
            List of AylaSchedule objects.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/devices/{device_key}/schedules.json"
        
        _LOGGER.debug(f"Fetching schedules for device key {device_key}")
        
        async with session.get(url, headers=self._get_headers()) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get schedules: {resp.status} - {text}")
            
            data = await resp.json()
        
        schedules = []
        for item in data:
            schedule_data = item.get("schedule", {})
            schedule = AylaSchedule.from_dict(schedule_data)
            
            # Fetch actions for each schedule
            if schedule.key:
                try:
                    actions = await self.get_schedule_actions(schedule.key)
                    schedule.actions = actions
                except AylaApiError as e:
                    _LOGGER.warning(f"Failed to fetch actions for schedule {schedule.key}: {e}")
            
            schedules.append(schedule)
        
        _LOGGER.info(f"Found {len(schedules)} schedules for device key {device_key}")
        return schedules
    
    async def get_schedule_actions(self, schedule_key: int) -> List[AylaScheduleAction]:
        """
        Get all actions for a schedule.
        
        Args:
            schedule_key: Schedule key from the server
            
        Returns:
            List of AylaScheduleAction objects.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedules/{schedule_key}/schedule_actions.json"
        
        _LOGGER.debug(f"Fetching actions for schedule {schedule_key}")
        
        async with session.get(url, headers=self._get_headers()) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get schedule actions: {resp.status} - {text}")
            
            data = await resp.json()
        
        actions = []
        for item in data:
            action_data = item.get("schedule_action", {})
            actions.append(AylaScheduleAction.from_dict(action_data))
        
        return actions
    
    async def create_schedule(self, device_key: int, schedule: AylaSchedule) -> AylaSchedule:
        """
        Create a new schedule for a device.
        
        Args:
            device_key: Ayla device key (numeric ID, NOT the DSN string!)
            schedule: AylaSchedule object to create
            
        Returns:
            Created AylaSchedule with server-assigned key.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/devices/{device_key}/schedules.json"
        
        payload = {"schedule": schedule.to_dict()}
        
        _LOGGER.debug(f"Creating schedule '{schedule.display_name}' for device key {device_key}")
        
        async with session.post(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise AylaApiError(f"Failed to create schedule: {resp.status} - {text}")
            
            data = await resp.json()
        
        created_schedule = AylaSchedule.from_dict(data.get("schedule", {}))
        
        # Create actions for the schedule
        for action in schedule.actions:
            created_action = await self.create_schedule_action(created_schedule.key, action)
            created_schedule.actions.append(created_action)
        
        _LOGGER.info(f"Created schedule '{created_schedule.display_name}' with key {created_schedule.key}")
        return created_schedule
    
    async def create_schedule_action(
        self, schedule_key: int, action: AylaScheduleAction
    ) -> AylaScheduleAction:
        """
        Create a new action for a schedule.
        
        Args:
            schedule_key: Schedule key from the server
            action: AylaScheduleAction to create
            
        Returns:
            Created AylaScheduleAction with server-assigned key.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedules/{schedule_key}/schedule_actions.json"
        
        payload = {"schedule_action": action.to_dict()}
        
        _LOGGER.debug(f"Creating action '{action.name}' for schedule {schedule_key}")
        
        async with session.post(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise AylaApiError(f"Failed to create schedule action: {resp.status} - {text}")
            
            data = await resp.json()
        
        return AylaScheduleAction.from_dict(data.get("schedule_action", {}))
    
    async def update_schedule(self, schedule: AylaSchedule) -> AylaSchedule:
        """
        Update an existing schedule.
        
        Args:
            schedule: AylaSchedule with key and updated values
            
        Returns:
            Updated AylaSchedule.
        """
        if not schedule.key:
            raise AylaApiError("Schedule key is required for update")
        
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedules/{schedule.key}.json"
        
        payload = {"schedule": schedule.to_dict()}
        
        _LOGGER.debug(f"Updating schedule {schedule.key} with payload: {payload}")
        _LOGGER.debug(f"Request URL: {url}")
        
        async with session.put(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise AylaApiError(f"Failed to update schedule: {resp.status} - {text}")
            
            data = await resp.json()
        
        updated = AylaSchedule.from_dict(data.get("schedule", {}))
        updated.actions = schedule.actions  # Preserve actions
        
        _LOGGER.info(f"Updated schedule {schedule.key}")
        return updated
    
    async def delete_schedule(self, schedule_key: int) -> bool:
        """
        Delete a schedule.
        
        Args:
            schedule_key: Schedule key to delete
            
        Returns:
            True if successful.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedules/{schedule_key}.json"
        
        _LOGGER.debug(f"Deleting schedule {schedule_key}")
        
        async with session.delete(url, headers=self._get_headers()) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                raise AylaApiError(f"Failed to delete schedule: {resp.status} - {text}")
        
        _LOGGER.info(f"Deleted schedule {schedule_key}")
        return True
    
    async def update_schedule_action(self, action: AylaScheduleAction) -> AylaScheduleAction:
        """
        Update an existing schedule action.
        
        Args:
            action: AylaScheduleAction with key and updated values
            
        Returns:
            Updated AylaScheduleAction.
        """
        if not action.key:
            raise AylaApiError("Action key is required for update")
        
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedule_actions/{action.key}.json"
        
        payload = {"schedule_action": action.to_dict()}
        
        _LOGGER.debug(f"Updating schedule action {action.key}")
        
        async with session.put(url, json=payload, headers=self._get_headers()) as resp:
            if resp.status not in (200, 201):
                text = await resp.text()
                raise AylaApiError(f"Failed to update schedule action: {resp.status} - {text}")
            
            data = await resp.json()
        
        return AylaScheduleAction.from_dict(data.get("schedule_action", {}))
    
    async def delete_schedule_action(self, action_key: int) -> bool:
        """
        Delete a schedule action.
        
        Args:
            action_key: Action key to delete
            
        Returns:
            True if successful.
        """
        if not self._auth_token:
            await self.login()
        
        session = await self._get_session()
        url = f"{AYLA_ADS_SERVICE}/apiv1/schedule_actions/{action_key}.json"
        
        _LOGGER.debug(f"Deleting schedule action {action_key}")
        
        async with session.delete(url, headers=self._get_headers()) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                raise AylaApiError(f"Failed to delete schedule action: {resp.status} - {text}")
        
        _LOGGER.info(f"Deleted schedule action {action_key}")
        return True


async def test_api():
    """Test function for the API client."""
    import os
    
    # Get credentials from environment or prompt
    email = os.environ.get("AERA_EMAIL", "")
    password = os.environ.get("AERA_PASSWORD", "")
    app_id = os.environ.get("AERA_APP_ID", "")
    app_secret = os.environ.get("AERA_APP_SECRET", "")
    
    if not all([email, password, app_id, app_secret]):
        print("Please set the following environment variables:")
        print("  AERA_EMAIL")
        print("  AERA_PASSWORD")
        print("  AERA_APP_ID")
        print("  AERA_APP_SECRET")
        return
    
    api = AylaApi(email, password, app_id, app_secret)
    
    try:
        # Login
        print("Logging in...")
        auth = await api.login()
        print(f"✓ Logged in successfully")
        print(f"  Access token: {auth.access_token[:20]}...")
        
        # Get devices
        print("\nFetching devices...")
        devices = await api.get_devices()
        print(f"✓ Found {len(devices)} device(s)")
        
        for device in devices:
            print(f"\n  Device: {device.product_name}")
            print(f"    DSN: {device.dsn}")
            print(f"    Model: {device.model}")
            print(f"    Status: {device.connection_status}")
            
            # Get properties
            print("    Properties:")
            props = await api.get_device_properties(device.dsn)
            for name, prop in props.items():
                print(f"      {name}: {prop['value']} ({prop['base_type']})")
        
    except AylaApiError as e:
        print(f"✗ Error: {e}")
    finally:
        await api.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_api())
