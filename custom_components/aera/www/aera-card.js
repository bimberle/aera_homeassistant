/**
 * Aera Diffuser Card for Home Assistant
 * A custom Lovelace card for controlling Aera smart fragrance diffusers.
 */

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

const CARD_VERSION = "1.0.0";

console.info(
  `%c AERA-CARD %c v${CARD_VERSION} `,
  "color: white; background: #7c4dff; font-weight: bold;",
  "color: #7c4dff; background: white; font-weight: bold;"
);

// Register the card
window.customCards = window.customCards || [];
window.customCards.push({
  type: "aera-card",
  name: "Aera Diffuser Card",
  description: "A card to control Aera smart fragrance diffusers",
  preview: true,
});

class AeraCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _activeSlider: { type: Boolean },
    };
  }

  static get styles() {
    return css`
      :host {
        --aera-primary: var(--primary-color, #7c4dff);
        --aera-bg: var(--card-background-color, #fff);
        --aera-text: var(--primary-text-color, #333);
        --aera-secondary: var(--secondary-text-color, #666);
      }

      ha-card {
        padding: 16px;
        border-radius: 12px;
        overflow: hidden;
      }

      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
      }

      .device-info {
        display: flex;
        flex-direction: column;
      }

      .device-name {
        font-size: 1.2em;
        font-weight: 500;
        color: var(--aera-text);
      }

      .room-name {
        font-size: 0.9em;
        color: var(--aera-secondary);
      }

      .fragrance-name {
        font-size: 0.85em;
        color: var(--aera-primary);
        margin-top: 2px;
      }

      .power-button {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid var(--aera-primary);
        background: transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
      }

      .power-button.on {
        background: var(--aera-primary);
      }

      .power-button.on svg {
        fill: white;
      }

      .power-button svg {
        width: 24px;
        height: 24px;
        fill: var(--aera-primary);
        transition: fill 0.3s ease;
      }

      .power-button:hover {
        transform: scale(1.05);
      }

      .diffuser-visual {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 120px;
        position: relative;
        margin: 16px 0;
      }

      .diffuser-icon {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, var(--aera-primary), #b388ff);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        z-index: 2;
      }

      .diffuser-icon svg {
        width: 40px;
        height: 40px;
        fill: white;
      }

      .mist-waves {
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        opacity: 0;
        transition: opacity 0.5s ease;
      }

      .mist-waves.active {
        opacity: 1;
      }

      .mist-wave {
        width: 20px;
        height: 20px;
        border: 2px solid var(--aera-primary);
        border-radius: 50%;
        animation: wave 2s ease-out infinite;
        opacity: 0;
      }

      .mist-wave:nth-child(1) {
        animation-delay: 0s;
      }
      .mist-wave:nth-child(2) {
        animation-delay: 0.4s;
      }
      .mist-wave:nth-child(3) {
        animation-delay: 0.8s;
      }

      @keyframes wave {
        0% {
          transform: scale(1);
          opacity: 0.8;
        }
        100% {
          transform: scale(3);
          opacity: 0;
        }
      }

      .intensity-control {
        margin: 16px 0;
      }

      .intensity-label {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-size: 0.9em;
        color: var(--aera-secondary);
      }

      .intensity-value {
        font-weight: 600;
        color: var(--aera-primary);
        font-size: 1.1em;
      }

      .intensity-slider {
        width: 100%;
        height: 8px;
        border-radius: 4px;
        background: linear-gradient(
          to right,
          var(--aera-primary) 0%,
          var(--aera-primary) var(--intensity-pct, 50%),
          #e0e0e0 var(--intensity-pct, 50%),
          #e0e0e0 100%
        );
        -webkit-appearance: none;
        appearance: none;
        cursor: pointer;
      }

      .intensity-slider::-webkit-slider-thumb {
        -webkit-appearance: none;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--aera-primary);
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
      }

      .intensity-slider::-moz-range-thumb {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--aera-primary);
        cursor: pointer;
        border: none;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
      }

      .session-info {
        background: var(--secondary-background-color, #f5f5f5);
        border-radius: 8px;
        padding: 12px;
        margin-top: 16px;
      }

      .session-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }

      .session-title {
        font-size: 0.9em;
        color: var(--aera-secondary);
      }

      .session-time {
        font-size: 1.2em;
        font-weight: 600;
        color: var(--aera-primary);
      }

      .session-buttons {
        display: flex;
        gap: 8px;
      }

      .session-btn {
        flex: 1;
        padding: 8px 12px;
        border: none;
        border-radius: 6px;
        font-size: 0.85em;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .session-btn.start {
        background: var(--aera-primary);
        color: white;
      }

      .session-btn.stop {
        background: #ff5252;
        color: white;
      }

      .session-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      }

      .status-row {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--divider-color, #e0e0e0);
        font-size: 0.85em;
      }

      .status-item {
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .status-label {
        color: var(--aera-secondary);
        margin-bottom: 4px;
      }

      .status-value {
        font-weight: 500;
        color: var(--aera-text);
      }

      .offline-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        z-index: 10;
      }

      .offline-text {
        color: white;
        font-size: 1.1em;
        font-weight: 500;
      }

      .unavailable {
        opacity: 0.5;
        pointer-events: none;
      }
    `;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity");
    }
    this.config = {
      show_session: true,
      show_fragrance: true,
      ...config,
    };
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("aera-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "",
      show_session: true,
      show_fragrance: true,
    };
  }

  _getEntityState() {
    if (!this.hass || !this.config.entity) return null;
    return this.hass.states[this.config.entity];
  }

  _isOn() {
    const state = this._getEntityState();
    return state && state.state === "on";
  }

  _isOnline() {
    const state = this._getEntityState();
    return state && state.state !== "unavailable";
  }

  _getIntensity() {
    const state = this._getEntityState();
    if (!state || !state.attributes) return 5;
    // Get from preset_mode which is "intensity_X"
    const preset = state.attributes.preset_mode;
    if (preset && preset.startsWith("intensity_")) {
      return parseInt(preset.split("_")[1], 10);
    }
    return state.attributes.intensity || 5;
  }

  _getRoomName() {
    const state = this._getEntityState();
    return state?.attributes?.room_name || "";
  }

  _getFragranceName() {
    const state = this._getEntityState();
    return state?.attributes?.fragrance_name || "";
  }

  _getSessionTimeLeft() {
    const state = this._getEntityState();
    return state?.attributes?.session_time_left || 0;
  }

  _isSessionActive() {
    const state = this._getEntityState();
    return state?.attributes?.session_active || false;
  }

  _formatTime(minutes) {
    if (!minutes) return "0:00";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}:${m.toString().padStart(2, "0")}` : `0:${m.toString().padStart(2, "0")}`;
  }

  _togglePower() {
    const service = this._isOn() ? "turn_off" : "turn_on";
    this.hass.callService("fan", service, {
      entity_id: this.config.entity,
    });
  }

  _setIntensity(e) {
    const value = parseInt(e.target.value, 10);
    this.hass.callService("fan", "set_preset_mode", {
      entity_id: this.config.entity,
      preset_mode: `intensity_${value}`,
    });
  }

  _startSession(duration) {
    this.hass.callService("aera", "start_session", {
      entity_id: this.config.entity,
      duration: duration,
    });
  }

  _stopSession() {
    this.hass.callService("aera", "stop_session", {
      entity_id: this.config.entity,
    });
  }

  render() {
    const state = this._getEntityState();
    if (!state) {
      return html`
        <ha-card>
          <div class="card-content">
            Entity not found: ${this.config.entity}
          </div>
        </ha-card>
      `;
    }

    const isOn = this._isOn();
    const isOnline = this._isOnline();
    const intensity = this._getIntensity();
    const roomName = this._getRoomName();
    const fragranceName = this._getFragranceName();
    const sessionTimeLeft = this._getSessionTimeLeft();
    const sessionActive = this._isSessionActive();

    return html`
      <ha-card class="${!isOnline ? "unavailable" : ""}">
        ${!isOnline
          ? html`
              <div class="offline-overlay">
                <span class="offline-text">Offline</span>
              </div>
            `
          : ""}

        <div class="card-header">
          <div class="device-info">
            <span class="device-name">${state.attributes.friendly_name || "Aera Diffuser"}</span>
            ${roomName ? html`<span class="room-name">${roomName}</span>` : ""}
            ${this.config.show_fragrance && fragranceName
              ? html`<span class="fragrance-name">🌸 ${fragranceName}</span>`
              : ""}
          </div>
          <button
            class="power-button ${isOn ? "on" : ""}"
            @click="${this._togglePower}"
          >
            <svg viewBox="0 0 24 24">
              <path
                d="M13 3h-2v10h2V3zm4.83 2.17l-1.42 1.42C17.99 7.86 19 9.81 19 12c0 3.87-3.13 7-7 7s-7-3.13-7-7c0-2.19 1.01-4.14 2.58-5.42L6.17 5.17C4.23 6.82 3 9.26 3 12c0 4.97 4.03 9 9 9s9-4.03 9-9c0-2.74-1.23-5.18-3.17-6.83z"
              />
            </svg>
          </button>
        </div>

        <div class="diffuser-visual">
          <div class="mist-waves ${isOn ? "active" : ""}">
            <div class="mist-wave"></div>
            <div class="mist-wave"></div>
            <div class="mist-wave"></div>
          </div>
          <div class="diffuser-icon">
            <svg viewBox="0 0 24 24">
              <path
                d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
              />
            </svg>
          </div>
        </div>

        <div class="intensity-control">
          <div class="intensity-label">
            <span>Intensität</span>
            <span class="intensity-value">${intensity}</span>
          </div>
          <input
            type="range"
            min="1"
            max="10"
            .value="${intensity}"
            class="intensity-slider"
            style="--intensity-pct: ${(intensity - 1) * 11.1}%"
            @change="${this._setIntensity}"
            ?disabled="${!isOn}"
          />
        </div>

        ${this.config.show_session
          ? html`
              <div class="session-info">
                <div class="session-header">
                  <span class="session-title">Session</span>
                  ${sessionActive
                    ? html`<span class="session-time">${this._formatTime(sessionTimeLeft)}</span>`
                    : ""}
                </div>
                <div class="session-buttons">
                  ${sessionActive
                    ? html`
                        <button class="session-btn stop" @click="${this._stopSession}">
                          Stoppen
                        </button>
                      `
                    : html`
                        <button class="session-btn start" @click="${() => this._startSession(120)}">
                          2h
                        </button>
                        <button class="session-btn start" @click="${() => this._startSession(240)}">
                          4h
                        </button>
                        <button class="session-btn start" @click="${() => this._startSession(480)}">
                          8h
                        </button>
                      `}
                </div>
              </div>
            `
          : ""}

        <div class="status-row">
          <div class="status-item">
            <span class="status-label">Status</span>
            <span class="status-value">${isOn ? "An" : "Aus"}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Modus</span>
            <span class="status-value">${state.attributes.mode || "Manual"}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Kartusche</span>
            <span class="status-value">${state.attributes.cartridge_usage || 0}%</span>
          </div>
        </div>
      </ha-card>
    `;
  }
}

// Card Editor
class AeraCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
    };
  }

  static get styles() {
    return css`
      .form-row {
        margin-bottom: 16px;
      }
      .form-row label {
        display: block;
        margin-bottom: 4px;
        font-weight: 500;
      }
      .form-row select,
      .form-row input {
        width: 100%;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
      }
      .checkbox-row {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    `;
  }

  setConfig(config) {
    this.config = config;
  }

  _getAeraEntities() {
    if (!this.hass) return [];
    return Object.keys(this.hass.states)
      .filter((eid) => eid.startsWith("fan.") && this.hass.states[eid].attributes.room_name !== undefined)
      .sort();
  }

  _valueChanged(e) {
    const target = e.target;
    const value = target.type === "checkbox" ? target.checked : target.value;
    const newConfig = { ...this.config, [target.configValue]: value };
    
    const event = new CustomEvent("config-changed", {
      detail: { config: newConfig },
      bubbles: true,
      composed: true,
    });
    this.dispatchEvent(event);
  }

  render() {
    if (!this.hass || !this.config) return html``;

    const entities = this._getAeraEntities();

    return html`
      <div class="form-row">
        <label>Entity</label>
        <select
          .configValue="${"entity"}"
          .value="${this.config.entity || ""}"
          @change="${this._valueChanged}"
        >
          <option value="">-- Select Entity --</option>
          ${entities.map(
            (eid) => html`<option value="${eid}" ?selected="${this.config.entity === eid}">${eid}</option>`
          )}
        </select>
      </div>

      <div class="form-row checkbox-row">
        <input
          type="checkbox"
          .configValue="${"show_session"}"
          .checked="${this.config.show_session !== false}"
          @change="${this._valueChanged}"
        />
        <label>Session-Steuerung anzeigen</label>
      </div>

      <div class="form-row checkbox-row">
        <input
          type="checkbox"
          .configValue="${"show_fragrance"}"
          .checked="${this.config.show_fragrance !== false}"
          @change="${this._valueChanged}"
        />
        <label>Duft-Name anzeigen</label>
      </div>
    `;
  }
}

customElements.define("aera-card", AeraCard);
customElements.define("aera-card-editor", AeraCardEditor);
