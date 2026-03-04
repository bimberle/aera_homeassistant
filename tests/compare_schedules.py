"""Compare schedules - find app-created vs API-created schedules."""
import asyncio
import sys
import os

# Add parent directory to path so we can import ayla_api as a package
sys.path.insert(0, "/Users/michi/Nextcloud/dev/aera_homeassistant")
os.chdir("/Users/michi/Nextcloud/dev/aera_homeassistant")

from ayla_api.aera import AeraApi

async def check():
    api = AeraApi("michael@kech.de", "$UUENb*UDjz#7&IUOh@k")
    await api.login()
    devices = await api.get_devices()
    kitchen = [d for d in devices if d.dsn == "AC000W041709779"][0]
    schedules = await kitchen.get_schedules()
    
    print("=== ALLE SCHEDULES MIT DATEN (Kitchen) ===\n")
    
    for s in schedules:
        # Zeige nur Schedules die aktiv sind ODER mindestens eine Action mit Value haben
        has_data = s.active or (s.actions and any(a.value for a in s.actions))
        if has_data:
            print(f"Schedule: {s.display_name} (key={s.key})")
            print(f"  Active: {s.active}")
            print(f"  Start: {s.start_time_each_day}")
            print(f"  End: {s.end_time_each_day}")
            print(f"  Days: {s.days_of_week}")
            print(f"  Direction: {s.direction}")
            print(f"  UTC: {s.utc}")
            print(f"  Actions ({len(s.actions)}):")
            for a in s.actions:
                print(f"    - {a.name}: {repr(a.value)} (base_type={a.base_type}, key={a.key})")
            print()
    
    await api.logout()

if __name__ == "__main__":
    asyncio.run(check())
