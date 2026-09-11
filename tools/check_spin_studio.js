#!/usr/bin/env node
// Run the spin studio's page script headlessly at one knob setting and dump what it computed:
// the sequence it built (G on its fine grid, the RF events) and the per-spin magnetisation at
// every step. tools/check_spin_studio.py then replays the SAME positions under the SAME sequence
// with dmipy_sim.replay_bloch and compares -- the studio is the one place on the site where the
// Bloch equation is integrated in JavaScript, so it is checked against the engine.
//
// Run: node tools/check_spin_studio.js '{"fam":"pgse","te":60,"pgse_b":1000,"relax":false}' out.json
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const PAGE = path.join(ROOT, 'docs', 'studio', 'bloch_pedagogy.html');
const html = fs.readFileSync(PAGE, 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));
const knobs = Object.assign({ fam: 'pgse', te: 60, gang: 90, ex: 90, re: 180, b1: 1, df: 0, relax: true,
                              pgse_b: 1000, pgse_del: 8, pgse_Dd: 30, pgste_b: 1000, pgste_del: 6, pgste_TM: 25,
                              ogse_b: 800, ogse_n: 2, gre_b: 0, cpmg_ne: 4 }, JSON.parse(process.argv[2] || '{}'));
const out = process.argv[3] || 'spin_studio_run.json';

// --- a minimal DOM: elements by id with a value, a canvas context that ignores drawing --------
class Ctx { }
for (const m of ['clearRect', 'fillRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill', 'arc', 'fillText',
                 'save', 'restore', 'translate', 'strokeRect', 'putImageData'])
  Ctx.prototype[m] = function () {};
Ctx.prototype.getImageData = () => ({});
class El {
  constructor(id) { this.id = id; this.value = knobs[id] !== undefined ? String(knobs[id]) : '0';
    this.checked = !!knobs[id]; this.textContent = ''; this.innerHTML = ''; this.style = {}; this.dataset = {};
    this.width = 200; this.height = 200; this.classList = { toggle() {} }; this.max = 0; }
  getContext() { return new Ctx(); }
  addEventListener() {}
}
const byId = {};
const document = {
  getElementById: id => byId[id] ??= new El(id),
  querySelector: () => new El('q'),
  querySelectorAll: () => [],
};
const sandbox = { document, console, JSON, Math, Object, Array, Float64Array, Number, String,
                  requestAnimationFrame: () => {}, setTimeout: () => {} };
vm.createContext(sandbox);
vm.runInContext(script + '\n;this.__x = {buildSeq, evolve, getSEQ: () => SEQ, getMH: () => MH, getGEOM: () => GEOM, setFam};', sandbox);
const x = sandbox.__x;
x.setFam(knobs.fam);                       // rebuild(): labels + evolve() at these knobs
const SEQ = x.getSEQ(), MH = x.getMH(), GEOM = x.getGEOM();
const n = SEQ.n, spins = GEOM.spins;
const M = MH.map(frame => frame.map(m => [Number(m[0].toFixed(6)), Number(m[1].toFixed(6)), Number(m[2].toFixed(6))]));
fs.writeFileSync(out, JSON.stringify({
  knobs, n, dt: SEQ.dt, TE: SEQ.TE, label: SEQ.label,
  G: SEQ.G, rf: SEQ.rf.map(e => ({ i0: e.i0, nsub: e.nsub, flip_rad: e.flip, axis_rad: e.ax })),
  store: SEQ.store, recall: SEQ.recall, echoes: SEQ.echoes,
  comps: spins.map(s => s.comp), M,
}));
console.log(`${SEQ.label}: n=${n} dt=${(SEQ.dt * 1e3).toFixed(3)} ms, ${spins.length} spins -> ${out}`);
