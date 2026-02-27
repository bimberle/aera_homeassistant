# Aera for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Eine HACS-Integration für Aera Smart Diffuser in Home Assistant.

## ✅ Features

- **Ein/Aus schalten** - Diffuser steuern
- **Intensität** - Stärke 1-10 einstellen
- **Sessions** - Timer-basierte Sitzungen (2h, 4h, 8h)
- **Duft setzen** - Für aeraMini manueller Duft-Code
- **Room Names** - Raumnamen aus der Aera App
- **Custom Card** - Schöne Lovelace-Karte (optional)

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

## Lovelace Card (optional)

Die Integration enthält eine schöne Custom Card.

### Card einrichten

1. Lovelace Dashboard → ⋮ → Ressourcen verwalten
2. Ressource hinzufügen:
   - URL: `/aera/aera-card.js`
   - Typ: JavaScript-Modul
3. Card zu deinem Dashboard hinzufügen:

```yaml
type: custom:aera-card
entity: fan.kitchen  # Deine Aera Entity
show_session: true
show_fragrance: true
```

### Card-Optionen

| Option | Default | Beschreibung |
|--------|---------|--------------|
| `entity` | - | Entity-ID des Aera Diffusers (erforderlich) |
| `show_session` | true | Session-Timer anzeigen |
| `show_fragrance` | true | Duft-Name anzeigen |

## Unterstützte Geräte

- **aera 3.1** - Mit automatischer Dufterkennung
- **aeraMini** - Mit manuellem Duft-Identifier

## Services

| Service | Beschreibung |
|---------|--------------|
| `aera.set_intensity` | Intensität setzen (1-10) |
| `aera.start_session` | Session starten (120/240/480 Min) |
| `aera.stop_session` | Aktive Session stoppen |
| `aera.set_fragrance` | Duft-Code setzen (aeraMini) |
| `aera.set_room_name` | Raumnamen ändern |

## Entwicklung

Siehe [DEVELOPMENT.md](DEVELOPMENT.md) für technische Details zur API.

## Lizenz

MIT License
