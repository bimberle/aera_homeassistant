#!/usr/bin/env python3
"""Find schedules with intensity 5."""
import asyncio
import sys
sys.path.insert(0, '/Users/michi/Nextcloud/dev/aera_homeassistant/custom_components/aera')
from ayla_api.aera import AeraApi

async def test():
    api = AeraApi('michael@kech.de', '$UUENb*UDjz#7&IUOh@k')
    await api.login()
    
    devices = await api.get_devices()
    kitchen = [d for d in devices if 'Kitchen' in d.name or 'Kitchen' in d.room_name][0]
    print(f'Kitchen Device: {kitchen.dsn}')
    
    schedules = await kitchen.get_schedules()
    
    print(f'\nSearching for schedules with intensity 5...\n')
    
    found = False
    for s in schedules:
        for a in s.actions:
            if 'intensity' in a.name.lower() and a.value == '5':
                status = 'ACTIVE' if s.active else 'inactive'
                print(f'[{status}] {s.display_name} (key={s.key})')
                print(f'    Time: {s.start_time_each_day} - {s.end_time_each_day}')
                print(f'    Days: {s.days_of_week}')
                print(f'    Intensity: {a.value}')
                found = True
    
    if not found:
        print('Keine Schedules mit Intensity 5 gefunden.')
    
    await api.close()

if __name__ == "__main__":
    asyncio.run(test())
