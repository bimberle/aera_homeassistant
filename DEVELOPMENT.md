# Aera Home Assistant Integration - Entwicklerdokumentation

## Übersicht

Diese Integration ermöglicht die Steuerung von **Aera Smart Fragrance Diffusers** über Home Assistant. Die Geräte kommunizieren über die **Ayla Networks IoT Platform**.

## Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    Home Assistant                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   fan.py    │  │ services.py │  │  coordinator.py │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
│         │                │                   │           │
│         └────────────────┼───────────────────┘           │
│                          ▼                               │
│              ┌───────────────────────┐                   │
│              │   ayla_api/aera.py    │                   │
│              │   (AeraDevice, AeraApi)│                  │
│              └───────────┬───────────┘                   │
│                          ▼                               │
│              ┌───────────────────────┐                   │
│              │  ayla_api/client.py   │                   │
│              │   (AylaApi - Low-Level)│                  │
│              └───────────┬───────────┘                   │
└──────────────────────────┼──────────────────────────────┘
                           ▼
              ┌───────────────────────┐
              │  Ayla Networks Cloud  │
              │  (user-field.ayla...) │
              └───────────────────────┘
```

## Ayla Networks API

### Authentifizierung

Die API verwendet OAuth-ähnliche Tokens. Credentials stammen aus der Aera Android APK:

```python
APP_ID = "android-id-id"
APP_SECRET = "android-id-oYOAkxPCU46_E04WxtwfOYatrUI"
```

**Login Endpoint:**
```
POST https://user-field.aylanetworks.com/users/sign_in.json
Body: {
  "user": {
    "email": "...",
    "password": "...",
    "application": {
      "app_id": "android-id-id",
      "app_secret": "..."
    }
  }
}
```

**Response enthält:**
- `access_token` - für API-Aufrufe
- `refresh_token` - zum Erneuern
- `expires_in` - Gültigkeit in Sekunden

### Geräte-API

**Geräte abrufen:**
```
GET https://ads-field.aylanetworks.com/apiv1/devices.json
Header: Authorization: auth_token <access_token>
```

**Properties abrufen:**
```
GET https://ads-field.aylanetworks.com/apiv1/dsns/<DSN>/properties.json
```

**Property setzen:**
```
POST https://ads-field.aylanetworks.com/apiv1/properties/<property_key>/datapoints.json
Body: {"datapoint": {"value": <value>}}
```

### Aera Device Properties

| Property | Typ | Beschreibung |
|----------|-----|--------------|
| `power_state` | int | 0=aus, 1=an (read-only) |
| `set_power_state` | int | 0=aus, 1=an (write) |
| `intensity_state` | int | 1-10, aktuelle Intensität |
| `set_intensity_manual` | int | 1-10, Intensität setzen |
| `mode_state` | int | 0=manual, 1=scheduled, 2=away |
| `session_state` | int | 0=keine Session, 1=Session aktiv |
| `session_time_left` | int | Verbleibende Zeit in Minuten |
| `set_session_length` | int | Session-Dauer (120/240/480 Min) |
| `cartridge_present` | int | 0=nein, 1=ja |
| `cartridge_usage` | int | Verbrauch in % |
| `fragrance_name` | str | Name des Dufts |
| `set_fragrance_identifier` | str | 3-Buchstaben Code (nur aeraMini) |

### Datum API (Metadaten)

Room Names und Display-Positionen werden NICHT in den Device Properties gespeichert, sondern in der **Ayla Datum API** - einem Key-Value Store für Benutzerdaten.

**Metadaten abrufen:**
```
GET https://user-field.aylanetworks.com/api/v1/users/data/device_data_table.json
```

**Response:**
```json
{
  "datum": {
    "key": "device_data_table",
    "value": "[{\"dsn\":\"AC000W027374342\",\"room_name\":\"Guest Room\",\"ordered_position\":0,\"schedule_order\":[]},{\"dsn\":\"AC000W041709779\",\"room_name\":\"Kitchen\",\"ordered_position\":1,\"schedule_order\":[]}]"
  }
}
```

**WICHTIG:** Der `value` ist ein **JSON-String innerhalb von JSON** - muss doppelt geparst werden!

**Metadaten setzen:**
```
PUT https://user-field.aylanetworks.com/api/v1/users/data/device_data_table.json
Body: {
  "datum": {
    "value": "<escaped-json-array>"
  }
}
```

## Gerätetypen

| Modell | OEM Model | Eigenschaften |
|--------|-----------|---------------|
| aeraMini | `aeraMini` | Kompakt, manueller Duft-Code erforderlich |
| aera 3.1 | `aera31` | Größer, automatische Dufterkennung |

## Code-Struktur

### ayla_api/client.py (Low-Level)

```python
@dataclass
class AeraDevice:
    dsn: str
    product_name: str
    model: str
    device_type: str
    connection_status: str
    room_name: str = ""           # Von Datum API
    ordered_position: int = 0     # Von Datum API

@dataclass
class DeviceMetadata:
    dsn: str
    room_name: str
    ordered_position: int
    schedule_order: list

class AylaApi:
    async def login() -> dict
    async def get_devices(include_metadata=True) -> list[AeraDevice]
    async def get_properties(dsn) -> dict
    async def set_property(dsn, name, value) -> bool
    async def get_device_metadata() -> list[DeviceMetadata]
    async def set_device_metadata(dsn, room_name, ordered_position) -> bool
```

### ayla_api/aera.py (High-Level)

```python
class AeraDevice:
    # Properties
    dsn: str
    name: str          # Returns room_name if set
    room_name: str
    ordered_position: int
    model: str
    state: AeraDeviceState
    
    # Methoden
    async def update() -> AeraDeviceState
    async def turn_on() -> bool
    async def turn_off() -> bool
    async def set_intensity(level: int) -> bool
    async def start_session(duration_minutes: int) -> bool
    async def stop_session() -> bool
    async def set_fragrance(fragrance_id: str) -> bool
    async def set_room_name(room_name: str) -> bool

class AeraApi:
    async def login() -> bool
    async def get_devices() -> list[AeraDevice]
    async def get_device(dsn) -> AeraDevice
    async def set_room_name(dsn, room_name) -> bool
    async def close()
```

## Home Assistant Integration

### Entities

- **Fan Entity** (`fan.py`): Hauptentität pro Gerät
  - Unterstützt: on/off, preset_modes (intensity 1-10)
  - Extra Attributes: room_name, dsn, session_time_left, etc.

### Services

| Service | Parameter | Beschreibung |
|---------|-----------|--------------|
| `aera.set_intensity` | entity_id, intensity | Intensität 1-10 setzen |
| `aera.start_session` | entity_id, duration | Session starten |
| `aera.stop_session` | entity_id | Session stoppen |
| `aera.set_fragrance` | entity_id, fragrance_id | Duft setzen (aeraMini) |
| `aera.set_room_name` | entity_id, room_name | Raumnamen setzen |

### Config Flow

Einfache Benutzer-Authentifizierung mit Email/Passwort.

## Bekannte Düfte (fragrances.py)

3-Buchstaben-Codes für aeraMini:
- `IDG` - Indigo
- `LVR` - Lavender
- `OBZ` - Ocean Breeze
- ... (siehe fragrances.py für vollständige Liste)

## Test-Geräte (Entwicklung)

- **AC000W027374342** (aeraMini) → "Guest Room"
- **AC000W041709779** (aera31) → "Kitchen"

## Wichtige Hinweise

1. **Token-Refresh:** Access Tokens laufen nach ~24h ab, müssen refreshed werden
2. **Rate Limiting:** Keine bekannten Limits, aber sparsam mit Anfragen
3. **Datum API URL:** `user-field.aylanetworks.com` (NICHT `user-field-eu`)
4. **JSON-in-JSON:** Datum API `value` ist escaped JSON String
5. **Property Keys:** Zum Setzen wird der `key` aus der Property-Response benötigt

## Versionen

- **v0.1.0** - Initiale Release mit Grundfunktionen
- **v0.2.0** - Room Name Support via Datum API
