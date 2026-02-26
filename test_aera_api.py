#!/usr/bin/env python3
"""
Test-Skript für die Aera API.
Teste Login und Geräteabfrage mit deinen echten Credentials.
"""

import asyncio
import os
from dotenv import load_dotenv

# Lade .env falls vorhanden
load_dotenv()

# Aera Credentials (aus APK extrahiert)
APP_ID = "android-id-id"
APP_SECRET = "android-id-oYOAkxPCU46_E04WxtwfOYatrUI"

# Deine Login-Daten
EMAIL = os.getenv("AERA_EMAIL", "")
PASSWORD = os.getenv("AERA_PASSWORD", "")

import aiohttp

AYLA_USER_SERVICE = "https://user-field.aylanetworks.com"
AYLA_ADS_SERVICE = "https://ads-field.aylanetworks.com"


async def test_login():
    """Teste den Login zur Ayla API."""
    
    if not EMAIL or not PASSWORD:
        print("=" * 60)
        print("AERA API TEST")
        print("=" * 60)
        print()
        print("Bitte gib deine Aera-Login-Daten ein:")
        print()
        email = input("E-Mail: ")
        password = input("Passwort: ")
    else:
        email = EMAIL
        password = PASSWORD
    
    print()
    print("Versuche Login...")
    print()
    
    login_data = {
        "user": {
            "email": email,
            "password": password,
            "application": {
                "app_id": APP_ID,
                "app_secret": APP_SECRET
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(
            f"{AYLA_USER_SERVICE}/users/sign_in.json",
            json=login_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print("✅ LOGIN ERFOLGREICH!")
                print()
                print(f"Access Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"Refresh Token: {data.get('refresh_token', 'N/A')[:50]}...")
                print(f"Expires in: {data.get('expires_in', 'N/A')} seconds")
                print(f"Role: {data.get('role', 'N/A')}")
                
                access_token = data.get("access_token")
                
                # Geräte abrufen
                print()
                print("=" * 60)
                print("GERÄTE ABRUFEN...")
                print("=" * 60)
                print()
                
                headers = {
                    "Authorization": f"auth_token {access_token}"
                }
                
                async with session.get(
                    f"{AYLA_ADS_SERVICE}/apiv1/devices.json",
                    headers=headers
                ) as devices_resp:
                    if devices_resp.status == 200:
                        devices = await devices_resp.json()
                        print(f"✅ {len(devices)} Gerät(e) gefunden!")
                        print()
                        
                        for i, device_wrapper in enumerate(devices, 1):
                            device = device_wrapper.get("device", {})
                            print(f"--- Gerät {i} ---")
                            print(f"  Name: {device.get('product_name', 'N/A')}")
                            print(f"  DSN: {device.get('dsn', 'N/A')}")
                            print(f"  Model: {device.get('model', 'N/A')}")
                            print(f"  OEM Model: {device.get('oem_model', 'N/A')}")
                            print(f"  Status: {device.get('connection_status', 'N/A')}")
                            print(f"  MAC: {device.get('mac', 'N/A')}")
                            print(f"  SW Version: {device.get('sw_version', 'N/A')}")
                            print()
                            
                            # Properties abrufen
                            dsn = device.get("dsn")
                            if dsn:
                                print(f"  Lade Properties für {dsn}...")
                                async with session.get(
                                    f"{AYLA_ADS_SERVICE}/apiv1/dsns/{dsn}/properties.json",
                                    headers=headers
                                ) as props_resp:
                                    if props_resp.status == 200:
                                        properties = await props_resp.json()
                                        print(f"  ✅ {len(properties)} Properties gefunden:")
                                        for prop_wrapper in properties[:15]:  # Nur erste 15 zeigen
                                            prop = prop_wrapper.get("property", {})
                                            name = prop.get("name", "?")
                                            value = prop.get("value", "?")
                                            print(f"    - {name}: {value}")
                                        if len(properties) > 15:
                                            print(f"    ... und {len(properties) - 15} weitere")
                                    else:
                                        print(f"  ❌ Properties-Fehler: {props_resp.status}")
                            print()
                    else:
                        error = await devices_resp.text()
                        print(f"❌ Geräte-Abruf fehlgeschlagen: {devices_resp.status}")
                        print(f"   {error}")
                
            elif resp.status == 401:
                error = await resp.json()
                print("❌ LOGIN FEHLGESCHLAGEN!")
                print(f"   {error.get('error', 'Unbekannter Fehler')}")
            else:
                error = await resp.text()
                print(f"❌ Unerwarteter Fehler: {resp.status}")
                print(f"   {error}")


if __name__ == "__main__":
    asyncio.run(test_login())
