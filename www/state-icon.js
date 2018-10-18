class StateIcon extends Polymer.Element {
  setConfig(config) {
    if (!this.content) {
      this.state = 'unavailable';
      this.content = document.createElement('hui-state-icon-element');
      this.appendChild(this.content);
    }
    this.entity = config.entity;
    this.content.setConfig(config);
  }

  set hass(hass) {
    this.content.hass = hass;
    if (this.content.shadowRoot) {
      let state = hass.states[this.entity];
      state = state ? state.state : 'unavailable';
      if (this.state !== state) {
        this.content.shadowRoot.querySelector('state-badge').$.icon.style.color = state == 'on' ? 'var(--paper-item-icon-active-color)' : '';
        this.state = state;
      }
    }
  }
}

customElements.define('state-icon', StateIcon);
