// imagemapper.js — Interactive image hotspot mapping

class ImageMapper {
  constructor(containerId, imageEl, readOnly = false) {
    this.container = document.getElementById(containerId);
    this.imageEl   = imageEl;
    this.readOnly  = readOnly;
    this.pins      = [];
    this.maxPins   = 8;
    this.canvas    = null;
    this.overlay   = null;
    this.init();
  }

  init() {
    // Wrap image in relative container
    const wrapper = document.createElement("div");
    wrapper.style.cssText = "position:relative; display:inline-block; width:100%;";
    this.imageEl.parentNode.insertBefore(wrapper, this.imageEl);
    wrapper.appendChild(this.imageEl);

    this.imageEl.style.cssText = "width:100%; display:block; border-radius:12px;";

    // Overlay for pins
    this.overlay = document.createElement("div");
    this.overlay.style.cssText = `
      position:absolute; top:0; left:0; width:100%; height:100%;
      pointer-events:${this.readOnly ? "none" : "auto"};
    `;
    wrapper.appendChild(this.overlay);

    if (!this.readOnly) {
      this.overlay.style.cursor = "crosshair";
      this.overlay.addEventListener("click", (e) => this.handleClick(e));
      this.overlay.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        this.showPinMenu(e);
      });
    }

    // Resize handler
    window.addEventListener("resize", () => this.redrawPins());
  }

  handleClick(e) {
    if (this.pins.length >= this.maxPins) {
      showToast(`Maximum ${this.maxPins} pins allowed`, "warning");
      return;
    }
    const rect = this.overlay.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width  * 100).toFixed(2);
    const y = ((e.clientY - rect.top)  / rect.height * 100).toFixed(2);
    this.showLabelInput(parseFloat(x), parseFloat(y));
  }

  showLabelInput(x, y) {
    // Remove existing modal if any
    const old = document.getElementById("pin-modal");
    if (old) old.remove();

    const modal = document.createElement("div");
    modal.id = "pin-modal";
    modal.style.cssText = `
      position:fixed; top:50%; left:50%; transform:translate(-50%,-50%);
      background:white; border-radius:16px; padding:24px; width:320px;
      box-shadow:0 20px 60px rgba(0,0,0,0.2); z-index:9999;
      font-family:'Poppins',sans-serif;
    `;
    modal.innerHTML = `
      <h3 style="margin:0 0 8px;font-size:16px;color:#111827;">📍 Describe this spot</h3>
      <p style="margin:0 0 16px;font-size:13px;color:#6B7280;">What's distinctive about this area?</p>
      <input id="pin-label-input" type="text" placeholder="e.g. Crack on top-right corner"
        style="width:100%;padding:10px 14px;border:1.5px solid #E5E7EB;border-radius:8px;
               font-family:'Poppins',sans-serif;font-size:14px;outline:none;box-sizing:border-box;
               transition:border-color 0.2s;"
        onfocus="this.style.borderColor='#2563EB'"
        onblur="this.style.borderColor='#E5E7EB'">
      <div style="display:flex;gap:10px;margin-top:16px;">
        <button id="pin-cancel" style="flex:1;padding:10px;border:1.5px solid #E5E7EB;
          background:white;border-radius:8px;cursor:pointer;font-family:'Poppins',sans-serif;
          font-size:14px;color:#6B7280;">Cancel</button>
        <button id="pin-confirm" style="flex:1;padding:10px;background:#2563EB;color:white;
          border:none;border-radius:8px;cursor:pointer;font-family:'Poppins',sans-serif;
          font-size:14px;font-weight:600;">Add Pin</button>
      </div>
    `;
    document.body.appendChild(modal);

    const backdrop = document.createElement("div");
    backdrop.id = "pin-backdrop";
    backdrop.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9998;";
    document.body.appendChild(backdrop);

    const input = document.getElementById("pin-label-input");
    input.focus();

    document.getElementById("pin-cancel").onclick = () => {
      modal.remove(); backdrop.remove();
    };
    backdrop.onclick = () => { modal.remove(); backdrop.remove(); };

    const confirm = () => {
      const label = input.value.trim();
      if (!label) { input.style.borderColor = "#EF4444"; return; }
      this.addPin(x, y, label);
      modal.remove(); backdrop.remove();
      this.updateCounter();
    };

    document.getElementById("pin-confirm").onclick = confirm;
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") confirm(); });
  }

  addPin(x, y, label) {
    const id = Date.now();
    this.pins.push({ id, x, y, label });
    this.renderPin({ id, x, y, label });
    this.updateCounter();
  }

  renderPin(pin) {
    const num  = this.pins.findIndex(p => p.id === pin.id) + 1;
    const elem = document.createElement("div");
    elem.dataset.pinId = pin.id;
    elem.style.cssText = `
      position:absolute;
      left:${pin.x}%; top:${pin.y}%;
      transform:translate(-50%,-50%);
      width:28px; height:28px;
      background:#F59E0B;
      border:2.5px solid white;
      border-radius:50%;
      display:flex; align-items:center; justify-content:center;
      color:white; font-weight:700; font-size:12px;
      font-family:'Poppins',sans-serif;
      cursor:${this.readOnly ? "pointer" : "pointer"};
      box-shadow:0 2px 8px rgba(0,0,0,0.25);
      transition:transform 0.2s, box-shadow 0.2s;
      z-index:10;
    `;
    elem.textContent = num;

    // Tooltip
    const tooltip = document.createElement("div");
    tooltip.style.cssText = `
      position:absolute; bottom:calc(100% + 8px); left:50%;
      transform:translateX(-50%);
      background:#111827; color:white; padding:6px 10px;
      border-radius:6px; font-size:12px; white-space:nowrap;
      font-family:'Poppins',sans-serif;
      pointer-events:none; opacity:0; transition:opacity 0.2s;
      z-index:20;
    `;
    tooltip.textContent = pin.label;
    elem.appendChild(tooltip);

    elem.addEventListener("mouseenter", () => {
      tooltip.style.opacity = "1";
      elem.style.transform = "translate(-50%,-50%) scale(1.2)";
      elem.style.boxShadow = "0 4px 16px rgba(0,0,0,0.3)";
    });
    elem.addEventListener("mouseleave", () => {
      tooltip.style.opacity = "0";
      elem.style.transform = "translate(-50%,-50%) scale(1)";
      elem.style.boxShadow = "0 2px 8px rgba(0,0,0,0.25)";
    });

    if (!this.readOnly) {
      elem.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.removePin(pin.id);
      });
    }

    this.overlay.appendChild(elem);
  }

  showPinMenu(e) {
    const rect   = this.overlay.getBoundingClientRect();
    const x      = ((e.clientX - rect.left) / rect.width  * 100);
    const y      = ((e.clientY - rect.top)  / rect.height * 100);
    const nearby = this.pins.find(p => Math.abs(p.x - x) < 5 && Math.abs(p.y - y) < 5);
    if (nearby) this.removePin(nearby.id);
  }

  removePin(id) {
    this.pins = this.pins.filter(p => p.id !== id);
    this.redrawPins();
    this.updateCounter();
    showToast("Pin removed", "info");
  }

  redrawPins() {
    this.overlay.innerHTML = "";
    this.pins.forEach(p => this.renderPin(p));
  }

  clearAll() {
    this.pins = [];
    this.overlay.innerHTML = "";
    this.updateCounter();
  }

  getPins() {
    return this.pins.map(({ x, y, label }) => ({ x, y, label }));
  }

  loadPins(hotspots) {
    this.pins = hotspots.map((h, i) => ({ ...h, id: i + 1 }));
    this.redrawPins();
  }

  updateCounter() {
    const counter = document.getElementById("pin-counter");
    if (counter) counter.textContent = `${this.pins.length}/${this.maxPins} pins`;
  }

  getLegendHTML() {
    if (!this.pins.length) return "";
    return `
      <div style="margin-top:16px;padding:16px;background:#F8F9FA;border-radius:12px;">
        <h4 style="margin:0 0 12px;font-size:14px;color:#374151;font-family:'Poppins',sans-serif;">
          📋 Item Details
        </h4>
        ${this.pins.map((p, i) => `
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
            <span style="width:24px;height:24px;background:#F59E0B;border-radius:50%;
              display:flex;align-items:center;justify-content:center;
              color:white;font-size:11px;font-weight:700;flex-shrink:0;
              font-family:'Poppins',sans-serif;">${i+1}</span>
            <span style="font-size:13px;color:#374151;font-family:'Poppins',sans-serif;">${p.label}</span>
          </div>
        `).join("")}
      </div>
    `;
  }
}
