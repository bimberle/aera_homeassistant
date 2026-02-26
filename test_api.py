#!/usr/bin/env python3
"""
Test script for the Aera/Ayla API.

Usage:
    1. First, extract app_id and app_secret from the Aera app using mitmproxy
    2. Set environment variables or edit the credentials below
    3. Run: python test_api.py
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayla_api import AylaApi, AylaApiError


# ============================================
# CREDENTIALS - Fill in after mitmproxy analysis
# ============================================
AERA_EMAIL = os.environ.get("AERA_EMAIL", "")
AERA_PASSWORD = os.environ.get("AERA_PASSWORD", "")
AERA_APP_ID = os.environ.get("AERA_APP_ID", "")
AERA_APP_SECRET = os.environ.get("AERA_APP_SECRET", "")
# ============================================


async def main():
    """Main test function."""
    print("=" * 60)
    print("Aera API Test")
    print("=" * 60)
    
    # Check credentials
    missing = []
    if not AERA_EMAIL:
        missing.append("AERA_EMAIL")
    if not AERA_PASSWORD:
        missing.append("AERA_PASSWORD")
    if not AERA_APP_ID:
        missing.append("AERA_APP_ID")
    if not AERA_APP_SECRET:
        missing.append("AERA_APP_SECRET")
    
    if missing:
        print("\n❌ Missing credentials!")
        print("\nPlease set the following environment variables:")
        for var in missing:
            print(f"  export {var}='...'")
        print("\nOr edit this file directly.")
        print("\nTo extract APP_ID and APP_SECRET:")
        print("  1. Enable mitmproxy certificate on your iPhone")
        print("  2. Open the Aera app and login")
        print("  3. Check mitmweb at http://127.0.0.1:8081")
        print("  4. Look for requests to user-field.aylanetworks.com")
        return
    
    # Create API client
    api = AylaApi(
        email=AERA_EMAIL,
        password=AERA_PASSWORD,
        app_id=AERA_APP_ID,
        app_secret=AERA_APP_SECRET,
    )
    
    try:
        # Step 1: Login
        print("\n📡 Step 1: Logging in...")
        auth = await api.login()
        print(f"   ✅ Success!")
        print(f"   Token: {auth.access_token[:30]}...")
        
        # Step 2: Get devices
        print("\n📡 Step 2: Fetching devices...")
        devices = await api.get_devices()
        print(f"   ✅ Found {len(devices)} device(s)")
        
        # Step 3: Get device details
        for i, device in enumerate(devices, 1):
            print(f"\n📱 Device {i}: {device.product_name}")
            print(f"   DSN: {device.dsn}")
            print(f"   Model: {device.model}")
            print(f"   Type: {device.device_type}")
            print(f"   Status: {'🟢 Online' if device.is_online else '🔴 Offline'}")
            
            if device.is_online:
                print(f"\n   Properties:")
                props = await api.get_device_properties(device.dsn)
                
                # Find interesting properties
                for name, prop in sorted(props.items()):
                    value = prop['value']
                    readonly = "📖" if prop['read_only'] else "✏️"
                    print(f"   {readonly} {name}: {value}")
        
        print("\n" + "=" * 60)
        print("✅ API test completed successfully!")
        print("=" * 60)
        
    except AylaApiError as e:
        print(f"\n❌ API Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
