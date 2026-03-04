"""Dump complete raw schedule data for comparison."""
import asyncio
import sys
import os
import json

sys.path.insert(0, "/Users/michi/Nextcloud/dev/aera_homeassistant")
os.chdir("/Users/michi/Nextcloud/dev/aera_homeassistant")

from ayla_api.aera import AeraApi

async def check():
    api = AeraApi("michael@kech.de", "$UUENb*UDjz#7&IUOh@k")
    await api.login()
    
    devices = await api.get_devices()
    kitchen = [d for d in devices if d.dsn == "AC000W041709779"][0]
    schedules = await kitchen.get_schedules()
    
    print("=== RAW SCHEDULE COMPARISON ===\n")
    
    for s in schedules:
        # Only show schedules with data
        if s.active or (s.actions and any(a.value for a in s.actions)):
            print(f"{'='*60}")
            print(f"Schedule: {s.display_name} (key={s.key})")
            print(f"{'='*60}")
            
            # Print all attributes
            for attr in dir(s):
                if not attr.startswith('_'):
                    try:
                        val = getattr(s, attr)
                        if not callable(val):
                            print(f"  {attr}: {repr(val)}")
                    except:
                        pass
            
            print(f"\n  Actions:")
            for a in s.actions:
                print(f"    Action: {a.name} = {repr(a.value)}")
                for attr in dir(a):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(a, attr)
                            if not callable(val):
                                print(f"      {attr}: {repr(val)}")
                        except:
                            pass
            print()

asyncio.run(check())
