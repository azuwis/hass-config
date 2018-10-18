class StateIcon extends Polymer.Element {
  setConfig(config) {
    this.entity = config.entity;
    this.element = document.createElement('hui-state-icon-element');
    this.element.setConfig(config);
    this.appendChild(this.element);
  }

  set hass(hass) {
    this.element.hass = hass;
    if (this.element.shadowRoot) {
      let state = hass.states[this.entity].state;
      this.element.shadowRoot.querySelector('state-badge').$.icon.style.color = state == 'on' ? 'var(--paper-item-icon-active-color)' : '';
    }
  }
}

customElements.define('state-icon', StateIcon);
