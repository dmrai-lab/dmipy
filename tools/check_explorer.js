#!/usr/bin/env node
// Run the sequence explorer's page script headlessly against its generated data.
//
// There is no browser in CI; this shims the little DOM the page touches (querySelector,
// elements with innerHTML/textContent/children/classList, a 2-D canvas context that records
// how much was drawn, fetch() from the local files) and executes the page's <script> as is.
// It walks every family and every grid point, so a page that throws on any knob setting, or
// draws nothing for a built sequence, fails here before it is deployed.
//
// Run: node tools/check_explorer.js        (exit status = number of failures)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const STUDIO = path.join(ROOT, 'docs', 'studio');
const html = fs.readFileSync(path.join(STUDIO, 'explorer.html'), 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

// --- a minimal DOM -------------------------------------------------------------------------
class Ctx {
  constructor() { this.ops = 0; }
}
for (const m of ['clearRect', 'fillRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill', 'arc',
                 'fillText', 'setLineDash', 'save', 'restore', 'translate', 'rotate']) {
  Ctx.prototype[m] = function () { if (m === 'stroke' || m === 'fillText' || m === 'fillRect') this.ops++; };
}
class El {
  constructor(tag) {
    this.tag = tag; this.children = []; this.dataset = {}; this.attrs = {}; this.style = {};
    this._inner = ''; this.textContent = ''; this.value = ''; this.selected = false;
    this._cls = new Set(); this.classList = { toggle: (c, on) => on ? this._cls.add(c) : this._cls.delete(c) };
    this.ctx = new Ctx(); this.clientWidth = 900;
  }
  get innerHTML() { return this._inner; }
  set innerHTML(v) { this._inner = v; if (v === '') this.children = []; }
  appendChild(c) { this.children.push(c); return c; }
  setAttribute(k, v) { this.attrs[k] = v; }
  getAttribute(k) { return this.attrs[k] ?? (k === 'height' ? '200' : null); }
  getContext() { return this.ctx; }
  getBoundingClientRect() { return { width: 900, height: 200 }; }
}
const els = {};
const document = {
  querySelector: (sel) => els[sel] ??= new El(sel),
  createElement: (tag) => new El(tag),
};
const window = { devicePixelRatio: 1, addEventListener() {} };
const fetch = async (rel) => {
  const data = fs.readFileSync(path.join(STUDIO, rel), 'utf8');
  return { json: async () => JSON.parse(data) };
};

// --- run the page ----------------------------------------------------------------------------
const sandbox = { document, window, fetch, console, JSON, Math, Object, Array, String, Number, parseFloat };
vm.createContext(sandbox);
const failures = [];
(async () => {
  await vm.runInContext(script, sandbox);                  // loads index.json and picks 'pgse'
  await new Promise(r => setTimeout(r, 50));
  const fam = els['#fam'];
  const idx = JSON.parse(fs.readFileSync(path.join(STUDIO, 'explorer_data', 'index.json'), 'utf8'));
  let n = 0;
  for (const name of Object.keys(idx.families)) {
    const btn = fam.children.find(b => b.dataset.f === name);
    await btn.onclick(); await new Promise(r => setTimeout(r, 20));
    const data = JSON.parse(fs.readFileSync(path.join(STUDIO, 'explorer_data', `${name}.json`), 'utf8'));
    const selects = els['#knobs'].children.filter(e => e.tag === 'select');
    for (const p of data.points) {
      n++;
      // set every select to this point's knob values and fire the change handlers
      const keys = Object.keys(data.knobs);
      try {
        keys.forEach((k, i) => { selects[i].value = JSON.stringify(p.knobs[k]); selects[i].onchange(); });
        const g = els['#cG'].ctx.ops, refusedShown = els['#msg'].innerHTML.includes('refused');
        if (p.refused && !refusedShown) failures.push(`${name} ${p.call}: refusal not shown`);
        if (!p.refused && g === 0) failures.push(`${name} ${p.call}: nothing drawn`);
        if (!p.refused && !els['#rd'].innerHTML.includes(String(p.seq.b_smm2))) failures.push(`${name} ${p.call}: b not in readout`);
        els['#cG'].ctx.ops = 0;
      } catch (e) {
        failures.push(`${name} ${p.call}: ${e.message}`);
      }
    }
  }
  console.log(`${n} grid points exercised across ${Object.keys(idx.families).length} families, ${failures.length} failure(s)`);
  for (const f of failures.slice(0, 20)) console.log('  ' + f);
  process.exit(failures.length ? 1 : 0);
})().catch(e => { console.error('page script threw:', e); process.exit(1); });
