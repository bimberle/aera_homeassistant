/**
 * Aera Diffuser Card for Home Assistant
 * Design based on the official Aera Android App
 */

const LitElement = Object.getPrototypeOf(
  customElements.get("ha-panel-lovelace")
);
const html = LitElement.prototype.html;
const css = LitElement.prototype.css;

const CARD_VERSION = "2.0.0";

console.info(
  `%c AERA-CARD %c v${CARD_VERSION} `,
  "color: white; background: #002360; font-weight: bold;",
  "color: #002360; background: white; font-weight: bold;"
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
    };
  }

  static get styles() {
    return css`
      :host {
        /* Aera App Colors */
        --aera-primary: #002360;
        --aera-white: #ffffff;
        --aera-off-white: #f6f6f6;
        --aera-pale-gray: #cccccc;
        --aera-light-gray: #888888;
        --aera-black: #000000;
        --aera-red: #ea5866;
      }

      ha-card {
        overflow: hidden;
        border-radius: 16px;
        background: var(--aera-white);
      }

      /* Header with fragrance image */
      .card-header {
        position: relative;
        height: 180px;
        background: linear-gradient(135deg, #e8e8e8 0%, #f6f6f6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }

      .card-header.has-image {
        background-size: cover;
        background-position: center;
      }

      .fragrance-icon {
        width: 80px;
        height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .fragrance-icon svg {
        width: 60px;
        height: 100px;
        fill: var(--aera-pale-gray);
      }

      .session-badge {
        position: absolute;
        bottom: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: var(--aera-primary);
        color: var(--aera-white);
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 0.5px;
        white-space: nowrap;
        z-index: 10;
      }

      .session-badge.inactive {
        display: none;
      }

      /* Device label */
      .device-label {
        text-align: center;
        padding: 20px 16px 8px;
      }

      .room-name {
        font-size: 18px;
        font-weight: 600;
        color: var(--aera-black);
        margin: 0;
      }

      .fragrance-name {
        font-size: 14px;
        color: var(--aera-light-gray);
        margin: 4px 0 0;
      }

      /* Intensity controls */
      .intensity-controls {
        padding: 16px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }

      .intensity-btn {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid var(--aera-primary);
        background: transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        flex-shrink: 0;
      }

      .intensity-btn:hover:not(:disabled) {
        background: var(--aera-primary);
      }

      .intensity-btn:hover:not(:disabled) svg {
        fill: var(--aera-white);
      }

      .intensity-btn:disabled {
        opacity: 0.3;
        cursor: not-allowed;
        border-color: var(--aera-pale-gray);
      }

      .intensity-btn svg {
        width: 24px;
        height: 24px;
        fill: var(--aera-primary);
        transition: fill 0.2s ease;
      }

      .intensity-btn:disabled svg {
        fill: var(--aera-pale-gray);
      }

      .intensity-display {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
      }

      .intensity-value {
        font-size: 28px;
        font-weight: 500;
        color: var(--aera-black);
        margin-bottom: 8px;
      }

      .intensity-dots {
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 6px;
        height: 24px;
      }

      .intensity-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--aera-pale-gray);
        transition: background 0.2s ease;
      }

      .intensity-dot.active {
        background: var(--aera-primary);
      }

      /* Wave pattern for dots */
      .intensity-dot:nth-child(1) { margin-bottom: 8px; }
      .intensity-dot:nth-child(2) { margin-bottom: 5px; }
      .intensity-dot:nth-child(3) { margin-bottom: 2px; }
      .intensity-dot:nth-child(4) { margin-bottom: 1px; }
      .intensity-dot:nth-child(5) { margin-bottom: 0px; }
      .intensity-dot:nth-child(6) { margin-bottom: 0px; }
      .intensity-dot:nth-child(7) { margin-bottom: 1px; }
      .intensity-dot:nth-child(8) { margin-bottom: 2px; }
      .intensity-dot:nth-child(9) { margin-bottom: 5px; }
      .intensity-dot:nth-child(10) { margin-bottom: 8px; }

      /* Power toggle */
      .power-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 16px;
      }

      .toggle-label {
        font-size: 14px;
        font-weight: 500;
        color: var(--aera-black);
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }

      .toggle-switch {
        position: relative;
        width: 52px;
        height: 28px;
        background: var(--aera-pale-gray);
        border-radius: 14px;
        cursor: pointer;
        transition: background 0.3s ease;
      }

      .toggle-switch.on {
        background: var(--aera-primary);
      }

      .toggle-switch::after {
        content: '';
        position: absolute;
        top: 2px;
        left: 2px;
        width: 24px;
        height: 24px;
        background: var(--aera-white);
        border-radius: 50%;
        transition: transform 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
      }

      .toggle-switch.on::after {
        transform: translateX(24px);
      }

      /* Session options */
      .session-options {
        background: var(--aera-off-white);
        padding: 16px 20px;
        margin: 0 16px 16px;
        border-radius: 12px;
      }

      .session-title {
        text-align: center;
        font-size: 14px;
        color: var(--aera-black);
        margin-bottom: 12px;
        letter-spacing: 0.5px;
      }

      .session-buttons {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
      }

      .session-time-btn {
        flex: 1;
        padding: 10px 8px;
        border: 2px solid var(--aera-primary);
        border-radius: 8px;
        background: transparent;
        color: var(--aera-primary);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .session-time-btn.selected {
        background: var(--aera-primary);
        color: var(--aera-white);
      }

      .session-time-btn:hover:not(.selected) {
        background: rgba(0, 35, 96, 0.1);
      }

      .session-action-btn {
        width: 100%;
        padding: 14px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        transition: all 0.2s ease;
      }

      .session-action-btn.start {
        background: var(--aera-primary);
        color: var(--aera-white);
      }

      .session-action-btn.start:disabled {
        background: var(--aera-pale-gray);
        cursor: not-allowed;
      }

      .session-action-btn.stop {
        background: var(--aera-white);
        color: var(--aera-black);
        border: 2px solid var(--aera-black);
      }

      .session-action-btn svg {
        width: 18px;
        height: 18px;
      }

      .session-action-btn.start svg {
        fill: var(--aera-white);
      }

      .session-action-btn.stop svg {
        fill: var(--aera-black);
      }

      /* Status info */
      .status-info {
        display: flex;
        justify-content: space-around;
        padding: 12px 16px 16px;
        border-top: 1px solid var(--aera-off-white);
      }

      .status-item {
        text-align: center;
      }

      .status-label {
        font-size: 11px;
        color: var(--aera-light-gray);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
      }

      .status-value {
        font-size: 14px;
        font-weight: 500;
        color: var(--aera-black);
      }

      /* Offline state */
      .offline-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.85);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 100;
        border-radius: 16px;
      }

      .offline-text {
        font-size: 16px;
        font-weight: 600;
        color: var(--aera-light-gray);
      }

      .card-wrapper {
        position: relative;
      }

      /* Low fragrance warning */
      .low-fragrance-warning {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px;
        color: var(--aera-light-gray);
        font-size: 12px;
      }

      .low-fragrance-warning svg {
        width: 16px;
        height: 16px;
        fill: var(--aera-red);
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
    this._selectedDuration = 240; // Default 4h
  }

  getCardSize() {
    return 5;
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
    const preset = state.attributes.preset_mode;
    if (preset && preset.startsWith("intensity_")) {
      return parseInt(preset.split("_")[1], 10);
    }
    return state.attributes.intensity || 5;
  }

  _getRoomName() {
    const state = this._getEntityState();
    return state?.attributes?.room_name || state?.attributes?.friendly_name || "Aera Diffuser";
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

  _getCartridgeUsage() {
    const state = this._getEntityState();
    return state?.attributes?.cartridge_usage || 0;
  }

  _formatTime(minutes) {
    if (!minutes) return "";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h > 0 && m > 0) return `${h}h ${m}min left`;
    if (h > 0) return `${h}h left`;
    return `${m}min left`;
  }

  _togglePower() {
    const service = this._isOn() ? "turn_off" : "turn_on";
    this.hass.callService("fan", service, {
      entity_id: this.config.entity,
    });
  }

  _setIntensity(delta) {
    const current = this._getIntensity();
    const newValue = Math.max(1, Math.min(10, current + delta));
    if (newValue !== current) {
      this.hass.callService("fan", "set_preset_mode", {
        entity_id: this.config.entity,
        preset_mode: `intensity_${newValue}`,
      });
    }
  }

  _selectDuration(duration) {
    this._selectedDuration = duration;
    this.requestUpdate();
  }

  _startSession() {
    this.hass.callService("aera", "start_session", {
      entity_id: this.config.entity,
      duration: this._selectedDuration,
    });
  }

  _stopSession() {
    this.hass.callService("aera", "stop_session", {
      entity_id: this.config.entity,
    });
  }

  _renderIntensityDots(intensity) {
    return html`
      <div class="intensity-dots">
        ${[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(
          (i) => html`<div class="intensity-dot ${i <= intensity ? "active" : ""}"></div>`
        )}
      </div>
    `;
  }

  _renderClockIcon() {
    return html`
      <svg viewBox="0 0 24 24">
        <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z"/>
      </svg>
    `;
  }

  _renderMinusIcon() {
    return html`
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
        <path d="M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    `;
  }

  _renderPlusIcon() {
    return html`
      <svg viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
        <path d="M12 8v8M8 12h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    `;
  }

  _renderCapsuleIcon() {
    return html`
      <svg viewBox="0 0 60 100">
        <ellipse cx="30" cy="20" rx="25" ry="18" fill="currentColor"/>
        <rect x="5" y="20" width="50" height="60" fill="currentColor"/>
        <ellipse cx="30" cy="80" rx="25" ry="18" fill="currentColor"/>
        <ellipse cx="30" cy="20" rx="20" ry="14" fill="rgba(255,255,255,0.3)"/>
      </svg>
    `;
  }

  render() {
    const state = this._getEntityState();
    if (!state) {
      return html`
        <ha-card>
          <div style="padding: 16px; text-align: center; color: #888;">
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
    const cartridgeUsage = this._getCartridgeUsage();

    return html`
      <ha-card>
        <div class="card-wrapper">
          ${!isOnline
            ? html`
                <div class="offline-overlay">
                  <span class="offline-text">Offline</span>
                </div>
              `
            : ""}

          <!-- Header with fragrance visual -->
          <div class="card-header">
            <div class="fragrance-icon">
              ${this._renderCapsuleIcon()}
            </div>
            <div class="session-badge ${sessionActive ? "" : "inactive"}">
              ${this._formatTime(sessionTimeLeft)}
            </div>
          </div>

          <!-- Device label -->
          <div class="device-label">
            <h3 class="room-name">${roomName}</h3>
            ${this.config.show_fragrance && fragranceName
              ? html`<p class="fragrance-name">${fragranceName}</p>`
              : ""}
          </div>

          <!-- Intensity controls -->
          <div class="intensity-controls">
            <button
              class="intensity-btn"
              @click="${() => this._setIntensity(-1)}"
              ?disabled="${!isOn || intensity <= 1}"
            >
              ${this._renderMinusIcon()}
            </button>

            <div class="intensity-display">
              <span class="intensity-value">${intensity}</span>
              ${this._renderIntensityDots(intensity)}
            </div>

            <button
              class="intensity-btn"
              @click="${() => this._setIntensity(1)}"
              ?disabled="${!isOn || intensity >= 10}"
            >
              ${this._renderPlusIcon()}
            </button>
          </div>

          <!-- Power toggle -->
          <div class="power-toggle">
            <span class="toggle-label">OFF</span>
            <div
              class="toggle-switch ${isOn ? "on" : ""}"
              @click="${this._togglePower}"
            ></div>
            <span class="toggle-label">ON</span>
          </div>

          <!-- Session options -->
          ${this.config.show_session
            ? html`
                <div class="session-options">
                  <div class="session-title">Session Timer</div>
                  <div class="session-buttons">
                    <button
                      class="session-time-btn ${this._selectedDuration === 120 ? "selected" : ""}"
                      @click="${() => this._selectDuration(120)}"
                      ?disabled="${sessionActive}"
                    >
                      2 hours
                    </button>
                    <button
                      class="session-time-btn ${this._selectedDuration === 240 ? "selected" : ""}"
                      @click="${() => this._selectDuration(240)}"
                      ?disabled="${sessionActive}"
                    >
                      4 hours
                    </button>
                    <button
                      class="session-time-btn ${this._selectedDuration === 480 ? "selected" : ""}"
                      @click="${() => this._selectDuration(480)}"
                      ?disabled="${sessionActive}"
                    >
                      8 hours
                    </button>
                  </div>
                  ${sessionActive
                    ? html`
                        <button class="session-action-btn stop" @click="${this._stopSession}">
                          ${this._renderClockIcon()}
                          End Session
                        </button>
                      `
                    : html`
                        <button
                          class="session-action-btn start"
                          @click="${this._startSession}"
                          ?disabled="${!isOn}"
                        >
                          ${this._renderClockIcon()}
                          Start Session
                        </button>
                      `}
                </div>
              `
            : ""}

          <!-- Low fragrance warning -->
          ${cartridgeUsage > 80
            ? html`
                <div class="low-fragrance-warning">
                  <svg viewBox="0 0 24 24">
                    <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                  </svg>
                  Low fragrance remaining
                </div>
              `
            : ""}

          <!-- Status info -->
          <div class="status-info">
            <div class="status-item">
              <div class="status-label">Status</div>
              <div class="status-value">${isOn ? "On" : "Off"}</div>
            </div>
            <div class="status-item">
              <div class="status-label">Intensity</div>
              <div class="status-value">${intensity}/10</div>
            </div>
            <div class="status-item">
              <div class="status-label">Cartridge</div>
              <div class="status-value">${100 - cartridgeUsage}%</div>
            </div>
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
      .form-row input[type="text"] {
        width: 100%;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
      }
      .checkbox-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      .checkbox-row label {
        margin: 0;
      }
    `;
  }

  setConfig(config) {
    this.config = config;
  }

  _getAeraEntities() {
    if (!this.hass) return [];
    return Object.keys(this.hass.states)
      .filter((eid) => eid.startsWith("fan."))
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

      <div class="checkbox-row">
        <input
          type="checkbox"
          .configValue="${"show_session"}"
          .checked="${this.config.show_session !== false}"
          @change="${this._valueChanged}"
        />
        <label>Show session controls</label>
      </div>

      <div class="checkbox-row">
        <input
          type="checkbox"
          .configValue="${"show_fragrance"}"
          .checked="${this.config.show_fragrance !== false}"
          @change="${this._valueChanged}"
        />
        <label>Show fragrance name</label>
      </div>
    `;
  }
}

customElements.define("aera-card", AeraCard);
customElements.define("aera-card-editor", AeraCardEditor);
