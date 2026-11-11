// Draggable dividers between the app's sections.
// Each divider sets a CSS custom property that the grid in styles.css reads.
// Sizes are remembered per browser (localStorage); double-click resets one.

(function () {
  const KEY = "annotation-explorer-layout";
  const STEP = 24; // px per arrow-key press
  const layout = document.querySelector(".layout");
  const workflow = document.querySelector(".workflow");

  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
  const save = (s) => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* storage unavailable */ } };
  const saved = load();
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  // Each divider: how to turn a pointer position into a size, and where the size goes.
  const dividers = {
    side: {
      el: document.getElementById("gutter-side"),
      axis: "x",
      target: layout,
      prop: "--side-w",
      // Width of the paper list in px.
      measure: () => document.querySelector(".sidebar").getBoundingClientRect().width,
      fromPointer(x) {
        const r = layout.getBoundingClientRect();
        const pad = parseFloat(getComputedStyle(layout).paddingLeft);
        return x - r.left - pad - 6;
      },
      // Leave the right-hand panels at least ~560px.
      limits: () => [240, Math.max(240, Math.min(layout.clientWidth * 0.5, layout.clientWidth - 590))],
      css: (v) => `${Math.round(v)}px`,
    },
    panels: {
      el: document.getElementById("gutter-panels"),
      axis: "y",
      target: layout,
      prop: "--top-fr",
      // Height of the abstract panel in px; stored as a ratio to the workflow panel.
      measure: () => document.querySelector(".panel-top").getBoundingClientRect().height,
      fromPointer(y) {
        return y - document.querySelector(".panel-top").getBoundingClientRect().top - 6;
      },
      limits() {
        const total = panelsTotal();
        return [120, total - 150];
      },
      css: (v) => `${(v / Math.max(1, panelsTotal() - v)).toFixed(3)}fr`,
    },
    workflow: {
      el: document.getElementById("gutter-workflow"),
      axis: "x",
      target: workflow,
      prop: "--diag-fr",
      // Width of the diagram in px; stored as a ratio to the step-details column.
      measure: () => document.querySelector(".diagram-wrap").getBoundingClientRect().width,
      fromPointer(x) {
        return x - workflow.getBoundingClientRect().left - 4;
      },
      limits: () => [260, workflow.clientWidth - 9 - 220],
      css: (v) => `${(v / Math.max(1, workflow.clientWidth - 9 - v)).toFixed(3)}fr`,
    },
  };

  function panelsTotal() {
    const top = document.querySelector(".panel-top").getBoundingClientRect();
    const bottom = document.querySelector(".panel-bottom").getBoundingClientRect();
    return bottom.bottom - top.top - 12;
  }

  function apply(name, px) {
    const d = dividers[name];
    const [lo, hi] = d.limits();
    const value = d.css(clamp(px, lo, Math.max(lo, hi)));
    d.target.style.setProperty(d.prop, value);
    return value;
  }

  // Restore saved sizes (stored as the CSS value itself).
  for (const [name, d] of Object.entries(dividers)) {
    if (saved[name]) d.target.style.setProperty(d.prop, saved[name]);
  }

  for (const [name, d] of Object.entries(dividers)) {
    const { el } = d;

    el.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return;
      e.preventDefault();
      try { el.setPointerCapture(e.pointerId); } catch { /* e.g. synthetic events */ }
      el.classList.add("dragging");
      document.body.classList.add("resizing", d.axis === "x" ? "col" : "row");
      const move = (ev) => apply(name, d.fromPointer(d.axis === "x" ? ev.clientX : ev.clientY));
      const up = () => {
        el.removeEventListener("pointermove", move);
        el.removeEventListener("pointerup", up);
        el.removeEventListener("pointercancel", up);
        el.classList.remove("dragging");
        document.body.classList.remove("resizing", "col", "row");
        saved[name] = d.target.style.getPropertyValue(d.prop);
        save(saved);
      };
      el.addEventListener("pointermove", move);
      el.addEventListener("pointerup", up);
      el.addEventListener("pointercancel", up);
    });

    el.addEventListener("keydown", (e) => {
      const keys = d.axis === "x" ? ["ArrowLeft", "ArrowRight"] : ["ArrowUp", "ArrowDown"];
      const i = keys.indexOf(e.key);
      if (i < 0) return;
      e.preventDefault();
      e.stopPropagation(); // don't also move the paper selection
      saved[name] = apply(name, d.measure() + (i ? STEP : -STEP));
      save(saved);
    });

    el.addEventListener("dblclick", () => {
      d.target.style.removeProperty(d.prop);
      delete saved[name];
      save(saved);
    });
  }

  // Keep a saved paper-list width sensible on load and when the window shrinks.
  function fitSide() {
    if (saved.side && dividers.side.el.offsetParent) {
      const [, max] = dividers.side.limits();
      if (dividers.side.measure() > max) apply("side", max);
    }
  }
  fitSide();
  window.addEventListener("resize", fitSide);
})();
