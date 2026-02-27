"""
Ayla Networks API Client for Aera Smart Diffusers.

This module provides a Python interface to communicate with Aera devices
through the Ayla Networks IoT platform.
"""

import aiohttp
import asyncio
import json
from dataclasses import dataclass
from typing import Optional
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
class AeraDevice:
    """Aera device representation."""
    dsn: str  # Device Serial Number
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
            device_meta = metadata.get(dsn)
            
            devices.append(AeraDevice(
                dsn=dsn,
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
