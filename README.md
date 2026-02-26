# Aera for Home Assistant

Eine HACS-Integration für Aera Smart Diffuser in Home Assistant.

## 🚧 Status: In Entwicklung

Diese Integration befindet sich in der Entwicklung. Der API-Client ist fertig, die Home Assistant Integration folgt.

## Unterstützte Geräte

- **aera31** (AC000W041709779) - Mit automatischer Dufterkennung
- **aeraMini** (AC000W027374342) - Mit manuellem Duft-Identifier

## Roadmap

- [x] Phase 1: API-Analyse
  - [x] Traffic-Analyse mit mitmproxy
  - [x] Ayla Networks API identifiziert
  - [x] App-Credentials aus APK extrahiert

- [x] Phase 2: API-Client
  - [x] Login implementiert & getestet
  - [x] Geräte abrufen getestet
  - [x] Properties lesen/schreiben getestet
  - [x] turn_on(), turn_off()
  - [x] set_intensity(1-10)
  - [x] start_session(120/240/480 min)
  - [x] stop_session()
  - [x] set_fragrance("IDG") für aeraMini
  - [x] Dynamische Duft-Liste von Contentful

- [ ] Phase 3: Home Assistant Integration
  - [ ] Config Flow
  - [ ] Device Registry
  - [ ] Entities (Fan, Sensor, etc.)
  - [ ] Services

## 📁 Wichtige Ressourcen

### Dekompilierte APK

**Location:** `./apk_analysis/aera_decompiled/`

Falls du etwas nicht weißt oder zusätzliche API-Informationen brauchst, **schau immer zuerst in der dekompilierten APK nach**:

```bash
# Nach Strings suchen
grep -r "suchbegriff" ./apk_analysis/aera_decompiled/

# Java-Klassen durchsuchen
grep -r "class.*Ayla" ./apk_analysis/aera_decompiled/sources/
grep -r "property" ./apk_analysis/aera_decompiled/sources/

# Contentful-Infos
grep -r "contentful\|bsswjwaepi0w" ./apk_analysis/aera_decompiled/
```

Die APK enthält:
- Ayla Networks Client-Implementierung
- API-Credentials (app_id, app_secret)
- Contentful CMS Credentials für Duft-Datenbank
- Property-Namen und Datentypen
- OEM-spezifische Konfiguration

## API-Credentials

### Ayla Networks (aus APK extrahiert)
```python
app_id = "android-id-id"
app_secret = "android-id-oYOAkxPCU46_E04WxtwfOYatrUI"
```

### Contentful CMS (für Duft-Katalog)
```python
space_id = "bsswjwaepi0w"
access_token = "UC4IVgBwitvaugwTZQLSvO28UcUdUumEvpOy4MejPUg"
```

## API-Dokumentation

Die Aera-Geräte nutzen die **Ayla Networks IoT-Plattform**:

- Dokumentation: https://docs.aylanetworks.com/reference
- User Service: `https://user-field.aylanetworks.com`
- Device Service: `https://ads-field.aylanetworks.com`

### Wichtige Device Properties

| Property | Typ | RW | Beschreibung |
|----------|-----|-----|--------------|
| `set_power_state` | boolean | RW | Ein/Aus |
| `set_intensity_manual` | integer | RW | Intensität 1-10 |
| `set_session_length` | integer | RW | Session in Minuten (120/240/480) |
| `set_fragrance_identifier` | string | RW | 3-Buchstaben-Code (aeraMini) |
| `intensity_state` | integer | RO | Aktuelle Intensität |
| `session_state` | integer | RO | 0=keine Session, 1=aktiv |
| `session_time_left` | integer | RO | Restzeit in Minuten |
| `cartridge_usage` | integer | RO | % verbraucht (aera31) |
| `fragrance_name` | string | RO | Erkannter Duft (aera31) |
| `pump_life_time` | integer | RO | Pump-Zyklen (aeraMini) |

### Session starten (wichtig!)

Um eine Session zu starten, muss diese Reihenfolge eingehalten werden:
1. Gerät ausschalten (`set_power_state = 0`)
2. Session-Länge setzen (`set_session_length = 120/240/480`)
3. Gerät einschalten (`set_power_state = 1`)

## Setup für Entwicklung

```bash
cd aera_homeassistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Lizenz

MIT License
