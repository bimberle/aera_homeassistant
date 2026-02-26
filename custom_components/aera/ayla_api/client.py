"""
Ayla Networks API Client for Aera Smart Diffusers.

This module provides a Python interface to communicate with Aera devices
through the Ayla Networks IoT platform.
"""

import aiohttp
import asyncio
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
class AeraDevice:
    """Aera device representation."""
    dsn: str  # Device Serial Number
    product_name: str
    model: str
    device_type: str
    connection_status: str
    properties: dict
    
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
    
    async def get_devices(self) -> list[AeraDevice]:
        """
        Get all devices associated with the user account.
        
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
                return await self.get_devices()
            if resp.status != 200:
                text = await resp.text()
                raise AylaApiError(f"Failed to get devices: {resp.status} - {text}")
            
            data = await resp.json()
        
        devices = []
        for item in data:
            device_data = item.get("device", {})
            devices.append(AeraDevice(
                dsn=device_data.get("dsn", ""),
                product_name=device_data.get("product_name", ""),
                model=device_data.get("model", ""),
                device_type=device_data.get("device_type", ""),
                connection_status=device_data.get("connection_status", "Offline"),
                properties={},
            ))
        
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
