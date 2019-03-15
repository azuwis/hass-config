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
      let badge = this.content.shadowRoot.querySelector('state-badge');
      if (badge) {
        let state = hass.states[this.entity];
        state = state ? state.state : 'unavailable';
        if (this.state !== state) {
          let icon = badge.shadowRoot.querySelector('ha-icon').shadowRoot.querySelector('svg');
          if (state == 'off') {
            icon.style.color = '';
          } else if (state == 'unavailable') {
            icon.style.color = 'var(--state-icon-unavailable-color)';
          } else {
            icon.style.color = 'var(--paper-item-icon-active-color)';
          }
        }
        this.state = state;
      }
    }
  }
}

customElements.define('state-icon', StateIcon);
