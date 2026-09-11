#!/usr/bin/env node
// Run the landing-page signal widget's script headlessly against its generated data: every
// substrate and both sweeps are drawn, and the readout names the numbers the data holds.
// Run: node tools/check_signal_widget.js       (exit status = number of failures)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const STUDIO = path.resolve(__dirname, '..', 'docs', 'studio');
const html = fs.readFileSync(path.join(STUDIO, 'signal.html'), 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

class Ctx { constructor() { this.ops = 0; } }
for (const m of ['clearRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill', 'arc', 'fillText', 'setLineDash'])
  Ctx.prototype[m] = function () { if (m === 'stroke' || m === 'fillText') this.ops++; };
class El {
  constructor(id) { this.id = id; this.children = []; this.dataset = {}; this.value = '2'; this.checked = true;
    this.textContent = ''; this.innerHTML = ''; this.style = {}; this.max = 0; this.ctx = new Ctx();
    this.classList = { toggle() {} }; }
  getContext() { return this.ctx; }
  getBoundingClientRect() { return { width: 600, height: 230 }; }
}
const els = {};
const document = { querySelector: s => els[s] ??= new El(s) };
els['#seq'] = new El('#seq');
els['#seq'].children = [Object.assign(new El('b0'), { dataset: { s: 'pgse' } }), Object.assign(new El('b1'), { dataset: { s: 'ogse' } })];
const fetch = async rel => ({ json: async () => JSON.parse(fs.readFileSync(path.join(STUDIO, rel), 'utf8')) });
const sandbox = { document, fetch, console, JSON, Math, Object, Array, String, Number, window: { devicePixelRatio: 1, addEventListener() {} } };
vm.createContext(sandbox);
const data = JSON.parse(fs.readFileSync(path.join(STUDIO, 'signal_data.json'), 'utf8'));
const failures = [];
(async () => {
  await vm.runInContext(script, sandbox);
  await new Promise(r => setTimeout(r, 30));
  const radii = Object.keys(data.substrates).filter(k => k !== 'free');
  for (const btn of els['#seq'].children) {
    btn.onclick();
    for (let i = 0; i < radii.length; i++) {
      els['#r'].value = String(i); els['#c'].ctx.ops = 0; els['#r'].oninput();
      const sub = data.substrates[radii[i]];
      if (els['#c'].ctx.ops === 0) failures.push(`${btn.dataset.s} ${radii[i]}: nothing drawn`);
      if (!els['#rv'].textContent.includes('µm')) failures.push(`${btn.dataset.s} ${radii[i]}: radius label missing`);
      if (btn.dataset.s === 'pgse' && !els['#rd'].innerHTML.includes(String(sub.pgse[data.b_smm2.indexOf(3000)])))
        failures.push(`pgse ${radii[i]}: readout does not quote the stored signal`);
    }
  }
  console.log(`${2 * radii.length} widget states exercised, ${failures.length} failure(s)`);
  failures.forEach(f => console.log('  ' + f));
  process.exit(failures.length ? 1 : 0);
})().catch(e => { console.error('widget script threw:', e); process.exit(1); });
