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

## HACS Release-Prozess (WICHTIG!)

Beim Erstellen einer neuen Version **IMMER** diese Schritte befolgen, damit HACS die neue Version erkennt:

### Integration (aera_homeassistant)
1. **Version in `custom_components/aera/manifest.json` aktualisieren** (z.B. `"version": "1.3.0"`)
2. Änderungen committen und pushen
3. **Git Tag erstellen:** `git tag v1.3.0`
4. **Tag pushen:** `git push origin v1.3.0`
5. **GitHub Release erstellen:** `gh release create v1.3.0 --title "v1.3.0 - Titel" --notes "Release Notes..."`

### Card (aera-card)
1. **Version in `package.json` aktualisieren** (z.B. `"version": "1.3.0"`)
2. **Build ausführen:** `npm run build`
3. **⚠️ WICHTIG: Kompilierte JS ins Root kopieren:** `cp dist/aera-card.js aera-card.js`
   - HACS lädt die Datei aus dem Repo-Root, NICHT aus dem Release-Asset!
4. Änderungen committen und pushen
5. **Git Tag erstellen:** `git tag v1.3.0`
6. **Tag pushen:** `git push origin v1.3.0`
7. **GitHub Release erstellen:** `gh release create v1.3.0 --title "v1.3.0 - Titel" --notes "Release Notes..."`
8. **JS-Datei als Asset hochladen:** `gh release upload v1.3.0 dist/aera-card.js`

### Checkliste vor Release
- [ ] Version in manifest.json/package.json aktualisiert
- [ ] Beide ayla_api Ordner synchron (Integration)
- [ ] Build erfolgreich (Card)
- [ ] **Card: `aera-card.js` im Root aktualisiert!** (HACS lädt von hier!)
- [ ] Git Tag erstellt und gepusht
- [ ] **GitHub Release erstellt** (HACS braucht einen echten Release, nicht nur einen Tag!)
- [ ] **Card: `dist/aera-card.js` als Release-Asset hochgeladen!**

## GitHub Repositories

- **Integration:** https://github.com/bimberle/aera_homeassistant
- **Card:** https://github.com/bimberle/aera-card
- **Workspace:** `/Users/michi/Nextcloud/dev/aera.code-workspace` (beide Projekte)

## WICHTIG: Service-Registrierung mit UI-Parametern

Damit Service-Parameter in Home Assistant's Developer Tools > Actions UI erscheinen, reicht `async_register_platform_entity_service()` NICHT aus! 

### Das Problem
- `async_register_platform_entity_service()` registriert nur den **Handler** (die Funktion)
- Die `services.yaml` wird bei Custom Integrations nicht automatisch für die UI geladen
- **Ohne explizites Schema sieht man keine Parameter-Felder in der UI!**

### Die Lösung: `async_set_service_schema()`

Nach **JEDER** Service-Registrierung muss `async_set_service_schema()` aufgerufen werden:

```python
from homeassistant.helpers.service import async_set_service_schema

# 1. Service registrieren (Handler)
service.async_register_platform_entity_service(
    hass, DOMAIN, "set_intensity",
    entity_domain=FAN_DOMAIN,
    schema={vol.Required("intensity"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10))},
    func="async_set_intensity_service",
)

# 2. UI-Schema registrieren (WICHTIG für Parameter in der UI!)
async_set_service_schema(hass, DOMAIN, "set_intensity", {
    "name": "Set Intensity",
    "description": "Set the fragrance intensity level (1-10).",
    "fields": {
        "intensity": {
            "name": "Intensity",
            "description": "Intensity level from 1 to 10",
            "required": True,
            "selector": {"number": {"min": 1, "max": 10, "step": 1, "mode": "slider"}}
        }
    },
    "target": {"entity": {"integration": "aera", "domain": "fan"}}
})
```

### Verfügbare Selectors
- `{"number": {"min": 1, "max": 10, "mode": "slider"}}` - Slider
- `{"number": {"mode": "box"}}` - Eingabefeld
- `{"text": {}}` - Textfeld
- `{"boolean": {}}` - Toggle
- `{"time": {}}` - Zeitauswahl
- `{"select": {"options": [{"label": "2h", "value": "2h"}, ...]}}` - Dropdown
- `{"select": {"multiple": True, "options": [...]}}` - Multi-Select

### Merke
- `services.yaml` ist für Custom Integrations optional (wird nicht automatisch geladen)
- `async_set_service_schema()` ist der Schlüssel für UI-Parameter!
- Wurde in v1.5.28 implementiert nach langer Debugging-Session
