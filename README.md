# Aera for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Eine HACS-Integration für Aera Smart Diffuser in Home Assistant.

## ✅ Features

- **Ein/Aus schalten** - Diffuser steuern
- **Intensität** - Stärke 1-10 einstellen
- **Sessions** - Timer-basierte Sitzungen (2h, 4h, 8h)
- **Duft setzen** - Für aeraMini manueller Duft-Code
- **Room Names** - Raumnamen aus der Aera App
- **Sensoren** - Intensität, Füllstand, Session-Status

## Installation

### HACS (empfohlen)

1. HACS öffnen → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/bimberle/aera_homeassistant`
3. Kategorie: Integration
4. Integration suchen und installieren
5. Home Assistant neustarten

### Manuell

1. `custom_components/aera/` in dein `config/custom_components/` kopieren
2. Home Assistant neustarten

## Konfiguration

1. Einstellungen → Geräte & Dienste → Integration hinzufügen
2. "Aera" suchen
3. Email und Passwort deines Aera-Kontos eingeben

## Lovelace Card (separat)

Für eine schöne Custom Card installiere die **Aera Card** separat via HACS:

👉 **[Aera Card](https://github.com/bimberle/aera-card)** - Custom Lovelace Card mit GUI-Editor

### Card Installation (HACS)

1. HACS → Frontend → ⋮ → Benutzerdefinierte Repositories
2. URL: `https://github.com/bimberle/aera-card`
3. Kategorie: Lovelace
4. "Aera Card" installieren

## Unterstützte Geräte

- **aera 3.1** - Mit automatischer Dufterkennung
- **aeraMini** - Mit manuellem Duft-Identifier

## Services

| Service | Beschreibung |
|---------|--------------|
| `aera.start_session` | Session starten (120/240/480 Min) |
| `aera.stop_session` | Aktive Session stoppen |
| `aera.set_fragrance` | Duft-Code setzen (aeraMini) |
| `aera.set_room_name` | Raumnamen ändern |

## Entities

Jeder Diffuser erstellt folgende Entities:

- **Fan** (`fan.{room_name}`) - Hauptsteuerung mit Power und Intensität
- **Sensor Intensity** - Aktuelle Intensitätsstufe
- **Sensor Fill Level** - Füllstand der Kartusche (nur aera31)
- **Sensor Session Time** - Verbleibende Session-Zeit
- **Sensor Fragrance** - Name des aktuellen Dufts

## Entwicklung

Siehe [DEVELOPMENT.md](DEVELOPMENT.md) für technische Details zur API.

## Lizenz

MIT License
