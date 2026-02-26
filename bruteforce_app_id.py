#!/usr/bin/env python3
"""
Brute-force script to find Aera app_id and app_secret.

Based on known Ayla app_id patterns from other integrations:
- Shark: ios_shark_prod-3A-id / ios_shark_prod-74tFWGNg34LQCmR0m45SsThqrqs
- FGLair: FGLair-eu-id / FGLair-eu-gpFbVBRoiJ8E3QWJ-QRULLL3j3U
- CJIOSP: CJIOSP-id / CJIOSP-Vb8MQL_lFiYQ7DKjN0eCFXznKZE

HTTP Response Codes:
- 404: Invalid app_id/app_secret
- 401: Valid app_id, invalid credentials  <-- This is what we want!
- 200: Success (login worked)
"""

import requests
import sys

# Ayla Networks endpoints
USER_FIELD_URL = "https://user-field.aylanetworks.com"

# Common app_id patterns to try for Aera/Prolitec
APP_ID_CANDIDATES = [
    # Based on Prolitec/Aera naming
    "aera-id",
    "Aera-id", 
    "AERA-id",
    "aera-field-id",
    "prolitec-id",
    "Prolitec-id",
    "PROLITEC-id",
    
    # iOS style
    "ios_aera_prod-id",
    "ios_aera-id",
    "ios_prolitec_prod-id",
    "ios_prolitec-id",
    
    # Android style
    "android_aera_prod-id",
    "android_aera-id",
    "android_prolitec_prod-id",
    "android_prolitec-id",
    
    # Field style (like user-field.aylanetworks.com suggests)
    "aera-field-id",
    "prolitec-field-id",
    "AeraField-id",
    "ProliField-id",
    
    # Smart home style
    "aera-smart-id",
    "aera-home-id",
    "aerahome-id",
    
    # OEM ID patterns seen in traffic
    "OEM::1234567",  # Placeholder - would need actual OEM ID
]

# Dummy app_secret for testing - we just want to see if app_id is valid
DUMMY_SECRET = "test-secret-12345"

# Test credentials (fake - we just want to see the error type)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


def test_app_id(app_id: str, app_secret: str = DUMMY_SECRET) -> dict:
    """Test if an app_id returns 401 (valid) or 404 (invalid)"""
    login_data = {
        "user": {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "application": {
                "app_id": app_id,
                "app_secret": app_secret
            }
        }
    }
    
    try:
        resp = requests.post(
            f"{USER_FIELD_URL}/users/sign_in.json",
            json=login_data,
            timeout=10
        )
        return {
            "app_id": app_id,
            "status_code": resp.status_code,
            "response": resp.text[:200]  # First 200 chars
        }
    except Exception as e:
        return {
            "app_id": app_id,
            "status_code": -1,
            "response": str(e)
        }


def main():
    print("=" * 60)
    print("Aera/Prolitec app_id Brute-Force Tester")
    print("=" * 60)
    print()
    print("Looking for 401 response (means app_id is VALID!)")
    print("404 = invalid app_id, 401 = valid app_id")
    print()
    
    valid_candidates = []
    
    for app_id in APP_ID_CANDIDATES:
        result = test_app_id(app_id)
        status = result["status_code"]
        
        # Color coding for terminal
        if status == 401:
            # VALID app_id! (wrong credentials but valid app)
            print(f"✅ {app_id}: {status} - VALID APP_ID!")
            valid_candidates.append(app_id)
        elif status == 404:
            print(f"❌ {app_id}: {status} - invalid")
        else:
            print(f"⚠️  {app_id}: {status} - {result['response'][:50]}")
    
    print()
    print("=" * 60)
    if valid_candidates:
        print("VALID APP_IDs FOUND:")
        for app_id in valid_candidates:
            print(f"  - {app_id}")
    else:
        print("No valid app_ids found with these patterns.")
        print()
        print("Next steps:")
        print("1. Download the Aera APK and decompile it")
        print("2. Search for 'app_id' or 'app_secret' in the code")
        print("3. Or capture traffic with a rooted Android device")


if __name__ == "__main__":
    main()
