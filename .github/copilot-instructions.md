# Copilot Instructions für Aera Home Assistant Integration

## Wichtig: Lies zuerst die Dokumentation!

Bevor du an diesem Projekt arbeitest, lies **unbedingt** die Datei `DEVELOPMENT.md` im Root-Verzeichnis. Sie enthält alle wichtigen Informationen:

- Architektur der Integration
- Ayla Networks API Details und Endpoints
- Device Properties und deren Bedeutung
- Datum API für Room Names (JSON-in-JSON!)
- Code-Struktur und Klassen

## Projekt-Überblick

Dies ist eine **Home Assistant HACS Integration** für Aera Smart Fragrance Diffusers. Die Geräte kommunizieren über die Ayla Networks IoT Platform.

## Code-Struktur

```
ayla_api/                      # Standalone Python Library
  client.py                    # Low-Level Ayla API Client
  
custom_components/aera/        # Home Assistant Integration
  ayla_api/                    # Kopie der Library (muss synchron bleiben!)
    client.py
    aera.py                    # High-Level AeraDevice/AeraApi
  fan.py                       # Fan Entity
  services.py                  # HA Services
  coordinator.py               # Data Update Coordinator
```

## Wichtige Hinweise

1. **Zwei ayla_api Ordner:** Es gibt `ayla_api/` (standalone) und `custom_components/aera/ayla_api/` - beide müssen synchron gehalten werden!

2. **Datum API für Metadaten:** Room Names werden NICHT in Device Properties gespeichert, sondern über die separate Datum API (`/api/v1/users/data/device_data_table.json`)

3. **JSON-in-JSON:** Die Datum API speichert den Value als escaped JSON String innerhalb von JSON

4. **API Credentials:** Aus der Android APK extrahiert, siehe DEVELOPMENT.md

## Test-Geräte

- AC000W027374342 (aeraMini) → "Guest Room"
- AC000W041709779 (aera31) → "Kitchen"
