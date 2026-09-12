#!/usr/bin/env node
// Run the brain page's script headlessly against its generated data and compare what it computes with what
// dmipy-sim computed: the real harmonics against dmipy_sim.replay.so3.real_sh on stored directions, and the
// page's composition against ph.replay on the stored check voxels at the tutorial's own scheme (and, when the
// field tables exist, at the stored field checks). The page never replays; this is the proof that its
// recombination is the engine's arithmetic.
//
// Run: node tools/check_brain.js        (exit status = number of failures)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const STUDIO = path.join(ROOT, 'docs', 'studio');
const html = fs.readFileSync(path.join(STUDIO, 'brain.html'), 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));

class Ctx { constructor() { this.ops = 0; } createImageData(w, h) { return { data: new Uint8ClampedArray(4 * w * h) }; } }
for (const m of ['clearRect', 'fillRect', 'beginPath', 'moveTo', 'lineTo', 'stroke', 'fill', 'arc', 'ellipse', 'fillText',
                 'setLineDash', 'save', 'restore', 'translate', 'rotate', 'closePath', 'putImageData', 'drawImage'])
  Ctx.prototype[m] = function () { if (m === 'drawImage' || m === 'stroke') this.ops++; };
class El {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.style = {}; this.attrs = {}; this._inner = '';
    this.textContent = ''; this.value = '0'; this.hidden = false; this.disabled = false; this.title = '';
    this._cls = new Set(); this.classList = { toggle: (c, on) => on ? this._cls.add(c) : this._cls.delete(c), add: c => this._cls.add(c), remove: c => this._cls.delete(c) };
    this.ctx = new Ctx(); this.width = 200; this.height = 200; this.max = '59'; }
  get innerHTML() { return this._inner; } set innerHTML(v) { this._inner = v; if (v === '') this.children = []; }
  appendChild(c) { this.children.push(c); return c; }
  querySelectorAll(sel) { return this.children.filter(c => sel === 'button' ? c.tag === 'button' : true); }
  getContext() { return this.ctx; }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.width, height: this.height }; }
}
const els = {};
const byData = [];
const document = {
  querySelector: (sel) => els[sel] ??= new El(sel.replace('#', '')),
  querySelectorAll: (sel) => byData,
  createElement: (tag) => new El(tag),
};
for (const id of ['#plane', '#mode']) { const p = document.querySelector(id); for (let i = 0; i < 3; i++) { const b = new El('button'); b.dataset = id === '#plane' ? { p: String(2 - i) } : { m: i ? 'field' : 'grad' }; p.appendChild(b); } }
const window = { devicePixelRatio: 1, addEventListener() {}, __brain: null };
const fetch = async (rel) => {
  const p = path.join(STUDIO, rel);
  if (rel.endsWith('.json')) return { json: async () => JSON.parse(fs.readFileSync(p, 'utf8')) };
  const buf = fs.readFileSync(p); return { arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) };
};
const sandbox = { document, window, fetch, console, JSON, Math, Object, Array, String, Number, parseFloat, isNaN, NaN, Infinity,
                  Float32Array, Int16Array, Uint8Array, Uint16Array, Int32Array, Int8Array, Uint8ClampedArray, ArrayBuffer, DataView };
vm.createContext(sandbox);
const failures = [];
const fail = (m) => { failures.push(m); console.log('FAIL', m); };
(async () => {
  await vm.runInContext(script, sandbox);
  for (let i = 0; i < 50 && !window.__brain; i++) await new Promise(r => setTimeout(r, 100));
  const B = window.__brain;
  if (!B) { fail('the page did not finish loading'); process.exit(1); }
  const idx = B.index;
  // 1. the harmonics
  let eY = 0;
  idx.sh.Y_check.dirs.forEach((d, i) => { const Y = B.realSH(d); idx.sh.Y_check.Y[i].forEach((y, k) => { eY = Math.max(eY, Math.abs(Y[k] - y)); }); });
  console.log(`real harmonics vs dmipy_sim.replay.so3.real_sh: max |diff| ${eY.toExponential(2)} on ${idx.sh.Y_check.dirs.length} directions`);
  if (!(eY < 1e-9)) fail(`harmonics differ by ${eY}`);
  // 2. the composition at the tutorial's scheme, on the stored voxels, against ph.replay
  const chk = idx.check, tol = chk.tol, bs = chk.scheme.b_smm2, gs = chk.scheme.dirs_image;
  let eS = 0, n = 0, worst = null;
  chk.voxels.forEach((v, vi) => { for (let m = 0; m < bs.length; m++) {
    const s = B.gradAt(v, gs[m], bs[m]); const ref = chk.S[vi][m]; const e = Math.abs(s - ref); n++;
    if (e > eS) { eS = e; worst = { v, m, s, ref }; } } });
  console.log(`composition vs ph.replay: max |diff| ${eS.toExponential(2)} over ${n} voxel-measurements (tol ${tol})`, worst);
  if (!(eS < tol)) fail(`composition differs from the engine by ${eS}`);
  // 3. the field tables, when present
  const F = B.field();
  if (F && F.checks && F.checks.length) {
    let eF = 0, nF = 0;
    for (const c of F.checks) { chk.voxels.slice(0, c.S.length).forEach((v, vi) => { c.meas.forEach((mi, j) => {
      const nd = F.dirs_scanner.length, shi = Math.floor(mi / nd), di = mi % nd;
      const s = B.fieldAt(v, c.tilt, F.B0_T.indexOf(c.B0), F.seqs.indexOf(c.seq), shi, di); const e = Math.abs(s - c.S[vi][j]); nF++; eF = Math.max(eF, e); }); }); }
    console.log(`field mode vs ph.replay: max |diff| ${eF.toExponential(2)} over ${nF} voxel-measurements`);
    if (!(eF < 2e-3)) fail(`field mode differs from the engine by ${eF}`);
  } else console.log('field tables: not present, skipped');
  // 4. the page draws every plane
  for (const p of [2, 1, 0]) { const b = els['#plane'].children.find(x => x.dataset.p === String(p)); await b.onclick(); if (els['#cS'].ctx.ops === 0) fail(`plane ${p}: nothing drawn`); els['#cS'].ctx.ops = 0; }
  console.log(failures.length ? `${failures.length} failure(s)` : 'brain page: all checks passed');
  process.exit(failures.length);
})().catch(e => { console.error(e); process.exit(1); });
