from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QLocale, Qt, QUrl
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..i18n.translator import LocalizationCatalog
from ..simulation.engine import (
    NationSimulationEngine,
    SimulationScenario,
    StochasticEventMatrix,
)

YEARS_PER_STEP_LIMIT: int = 1000

STATUS_TEXT_KEYS: tuple[str, ...] = (
    "status_year",
    "status_idle",
    "status_metrics",
    "events_idle",
    "years_step_label",
    "btn_advance_years",
    "scenario_label",
    "btn_export_csv",
    "btn_export_json",
)

VIEWER_TEXT_KEYS: tuple[str, ...] = (
    "number_locale",
    "title",
    "ctrl_hint",
    "hud_cycle",
    "hud_year",
    "hud_population",
    "hud_citizens",
    "hud_metrics",
    "hud_hdi",
    "hud_gini",
    "hud_employment",
    "hud_hint",
    "hud_history",
    "legend_title",
    "legend_towers_title",
    "legend_towers_text",
    "legend_scale_low",
    "legend_scale_high",
    "legend_rings_title",
    "legend_rings_text",
    "legend_particles_title",
    "legend_particles_text",
    "glossary_title",
    "gl_population",
    "gl_citizens",
    "gl_hdi",
    "gl_gini",
    "gl_employment",
    "inspector_title",
    "inspector_click_hint",
    "inspector_close",
    "inspector_workforce",
    "inspector_events",
    "inspector_no_events",
    "ev_title",
    "ev_idle",
    "label_hdi",
    "label_gini",
    "label_pop",
)

_WEBENGINE_UNAVAILABLE_MESSAGE = (
    "3D visualisation requires the PySide6-WebEngine module.\n"
    "The simulation engine is active — advance years to see Python-side metrics."
)

_THREE_JS_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #16110E; color: #F4EAD8; font-family: monospace;
       overflow: hidden; width: 100vw; height: 100vh; }
canvas { display: block; position: absolute; top: 0; left: 0; }

#hud {
  position: absolute; top: 12px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.92); border: 1px solid #3a2e24;
  padding: 10px 14px; border-radius: 4px;
  width: clamp(170px, 22vw, 260px);
}
#hud .section { font-size: clamp(7px,0.85vw,10px); color: #7a6a5a;
                letter-spacing: 1px; margin-bottom: 5px; margin-top: 8px; }
#hud .section:first-child { margin-top: 0; }
#hud .row { font-size: clamp(8px,1vw,12px); color: #C89B6D;
            margin-bottom: 3px; display: flex;
            justify-content: space-between; gap: 8px; }
#hud .val  { color: #F4EAD8; font-weight: bold; }
#hud .hint { font-size: clamp(7px,0.85vw,10px); color: #7a6a5a;
             margin-top: 6px; font-style: italic; }
#history-chart {
  display: block; width: 100%; height: 50px;
  margin-top: 6px; border: 1px solid #3a2e24;
  border-radius: 2px; background: #120d0a;
}

#inspector {
  position: absolute; top: 12px; right: 54px; z-index: 12;
  background: rgba(22,17,14,0.95); border: 1px solid #C89B6D;
  padding: 10px 14px; border-radius: 4px;
  width: clamp(200px, 24vw, 320px); max-height: 280px; overflow-y: auto;
  box-shadow: 0 4px 12px rgba(0,0,0,0.6);
}
#inspector .ins-hdr { display: flex; justify-content: space-between; align-items: center;
                      font-size: clamp(8px,1vw,12px); font-weight: bold; color: #F4EAD8;
                      border-bottom: 1px solid #3a2e24; padding-bottom: 5px; margin-bottom: 6px; }
#inspector #ins-close { background: none; border: none; color: #C89B6D; font-size: 16px;
                        cursor: pointer; line-height: 1; padding: 0 4px; font-family: monospace; }
#inspector #ins-close:hover { color: #F4EAD8; }
#inspector .ins-row { font-size: clamp(7px,0.85vw,11px); color: #C89B6D; margin-bottom: 3px;
                      display: flex; justify-content: space-between; }
#inspector .ins-val { color: #F4EAD8; font-weight: bold; }
#inspector .ins-sub { font-size: clamp(7px,0.8vw,10px); color: #7a6a5a; letter-spacing: 1px;
                      margin-top: 6px; margin-bottom: 3px; text-transform: uppercase; }
#inspector .ins-ev-line { font-size: clamp(7px,0.8vw,10px); color: #84A97C; line-height: 1.3; margin-bottom: 2px; }

#legend {
  position: absolute; bottom: 44px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.92); border: 1px solid #3a2e24;
  padding: 8px 12px; border-radius: 4px;
  width: clamp(220px, 28vw, 350px); max-height: max(120px, calc(100vh - 290px));
  overflow-y: auto; scrollbar-width: thin; scrollbar-color: #5C4335 #16110E;
}
#legend .leg-hdr { display: flex; justify-content: space-between; cursor: pointer;
                   user-select: none; font-size: clamp(7px,0.85vw,10px);
                   color: #C89B6D; letter-spacing: 1px; }
#legend.collapsed .leg-body { display: none; }
#legend .leg-body { margin-top: 8px; }
#legend .leg-item { margin-bottom: 9px; }
#legend .leg-title { display: flex; align-items: center; gap: 8px; margin-bottom: 3px;
                     font-size: clamp(8px,0.95vw,12px); font-weight: bold; color: #F4EAD8; }
#legend .leg-text { font-size: clamp(7px,0.85vw,11px); line-height: 1.4; color: #9a8a7a; }
#legend .scale { display: flex; justify-content: space-between; margin-top: 3px;
                 font-size: clamp(7px,0.8vw,10px); color: #7a6a5a; }
#legend .sw-grad { width: 34px; height: 10px; border-radius: 2px; flex-shrink: 0;
                   background: linear-gradient(90deg,#C26653,#C89B6D,#84A97C); }
#legend .sw-ring { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0;
                   border: 2px solid rgba(200,155,109,0.85); }
#legend .sw-dots { display: inline-flex; gap: 3px; flex-shrink: 0; }
#legend .sw-dots i { width: 5px; height: 5px; border-radius: 50%; display: inline-block; }
#legend .gloss { border-top: 1px solid #3a2e24; padding-top: 7px; }
#legend .gloss-hdr { font-size: clamp(7px,0.85vw,10px); color: #C89B6D;
                     letter-spacing: 1px; margin-bottom: 5px; }
#legend .gl-item { font-size: clamp(7px,0.85vw,11px); line-height: 1.4;
                   color: #9a8a7a; margin-bottom: 5px; }
#legend .gl-item b { color: #C89B6D; }

#events {
  position: absolute; bottom: 44px; right: 52px; z-index: 10;
  background: rgba(22,17,14,0.90); border: 1px solid #3a2e24;
  padding: 8px 12px; border-radius: 4px;
  width: clamp(180px,28vw,370px); max-height: 150px; overflow: hidden;
}
#events .ev-hdr { font-size: clamp(7px,0.85vw,10px); color: #C89B6D;
                  letter-spacing: 1px; margin-bottom: 5px; }
#events .ev-line { font-size: clamp(7px,0.85vw,11px); color: #84A97C;
                   margin-bottom: 3px; line-height: 1.4; }

#title {
  position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
  z-index: 10; color: #C89B6D; font-size: clamp(8px,1vw,12px);
  letter-spacing: 3px; text-transform: uppercase;
  pointer-events: none; white-space: nowrap;
}

#zoom {
  position: absolute; top: 50%; right: 12px; transform: translateY(-50%);
  z-index: 10; display: flex; flex-direction: column; gap: 6px;
}
#zoom button {
  width: 34px; height: 34px; background: rgba(22,17,14,0.90);
  border: 1px solid #3a2e24; border-radius: 4px; color: #C89B6D;
  font-size: 20px; line-height: 1; cursor: pointer; font-family: monospace;
  display: flex; align-items: center; justify-content: center;
}
#zoom button:hover { background: rgba(60,40,20,0.95); color: #F4EAD8; }

#ctrl-hint {
  position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
  z-index: 10; background: rgba(22,17,14,0.80); border: 1px solid #3a2e24;
  padding: 4px 14px; border-radius: 20px;
  font-size: clamp(7px,0.8vw,10px); color: #7a6a5a;
  white-space: nowrap; pointer-events: none; letter-spacing: 0.5px;
}
</style>
</head>
<body>
<div id="title" data-i18n="title"></div>
<div id="zoom">
  <button id="zoom-in"  title="Zoom In (+)">+</button>
  <button id="zoom-out" title="Zoom Out (-)">&#8722;</button>
</div>
<div id="hud">
  <div class="section" data-i18n="hud_cycle"></div>
  <div class="row"><span data-i18n="hud_year"></span><span class="val" id="v-year">1</span></div>
  <div class="row"><span data-i18n="hud_population"></span><span class="val" id="v-pop">—</span></div>
  <div class="row"><span data-i18n="hud_citizens"></span><span class="val" id="v-drawn">0</span></div>
  <div class="section" data-i18n="hud_metrics"></div>
  <div class="row"><span data-i18n="hud_hdi"></span><span class="val" id="v-hdi">—</span></div>
  <div class="row"><span data-i18n="hud_gini"></span><span class="val" id="v-gini">—</span></div>
  <div class="row"><span data-i18n="hud_employment"></span><span class="val" id="v-emp">—</span></div>
  <div class="hint" id="v-hint" data-i18n="hud_hint"></div>
  <div class="section" data-i18n="hud_history"></div>
  <canvas id="history-chart" width="240" height="50"></canvas>
</div>
<div id="inspector" style="display:none;">
  <div class="ins-hdr"><span id="ins-name">—</span><button id="ins-close" title="Close">&times;</button></div>
  <div class="ins-row"><span>ID</span><span class="ins-val" id="ins-id">—</span></div>
  <div class="ins-row"><span data-i18n="hud_hdi"></span><span class="ins-val" id="ins-hdi">—</span></div>
  <div class="ins-row"><span data-i18n="hud_gini"></span><span class="ins-val" id="ins-gini">—</span></div>
  <div class="ins-row"><span data-i18n="hud_population"></span><span class="ins-val" id="ins-pop">—</span></div>
  <div class="ins-row"><span data-i18n="inspector_workforce"></span><span class="ins-val" id="ins-work">—</span></div>
  <div class="ins-sub" data-i18n="inspector_events"></div>
  <div id="ins-events"></div>
</div>
<div id="legend">
  <div class="leg-hdr" id="leg-toggle"><span data-i18n="legend_title"></span><span id="leg-caret">&#9662;</span></div>
  <div class="leg-body">
    <div class="leg-item">
      <div class="leg-title"><span class="sw-grad"></span><span data-i18n="legend_towers_title"></span></div>
      <div class="leg-text" data-i18n="legend_towers_text"></div>
      <div class="scale"><span data-i18n="legend_scale_low"></span><span data-i18n="legend_scale_high"></span></div>
    </div>
    <div class="leg-item">
      <div class="leg-title"><span class="sw-ring"></span><span data-i18n="legend_rings_title"></span></div>
      <div class="leg-text" data-i18n="legend_rings_text"></div>
    </div>
    <div class="leg-item">
      <div class="leg-title">
        <span class="sw-dots"><i style="background:#9E6633"></i><i style="background:#C28F52"></i><i style="background:#E8C29E"></i></span>
        <span data-i18n="legend_particles_title"></span>
      </div>
      <div class="leg-text" data-i18n="legend_particles_text"></div>
    </div>
    <div class="gloss">
      <div class="gloss-hdr" data-i18n="glossary_title"></div>
      <div class="gl-item" data-i18n-term="gl_population"></div>
      <div class="gl-item" data-i18n-term="gl_citizens"></div>
      <div class="gl-item" data-i18n-term="gl_hdi"></div>
      <div class="gl-item" data-i18n-term="gl_gini"></div>
      <div class="gl-item" data-i18n-term="gl_employment"></div>
    </div>
  </div>
</div>
<div id="events">
  <div class="ev-hdr" data-i18n="ev_title"></div>
  <div id="ev-body"><div class="ev-line" style="color:#7a6a5a" data-i18n="ev_idle"></div></div>
</div>
<div id="ctrl-hint" data-i18n="ctrl_hint"></div>
<script>
window.__i18n = {};
const historySnapshots = [];
function T(key) { return window.__i18n[key] !== undefined ? window.__i18n[key] : ''; }
function numLocale() { return window.__i18n.number_locale || 'en-GB'; }
function fmtInt(n) { return Number(n || 0).toLocaleString(numLocale()); }
function fmtDec(v, digits) {
  return Number(v).toLocaleString(numLocale(),
    {minimumFractionDigits: digits, maximumFractionDigits: digits});
}
function setText(id, text) { const e = document.getElementById(id); if (e) e.textContent = text; }

function drawHistoryChart() {
  const cv = document.getElementById('history-chart');
  if (!cv) return;
  const ctx = cv.getContext('2d');
  const w = cv.width, h = cv.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = '#120d0a';
  ctx.fillRect(0, 0, w, h);
  if (historySnapshots.length < 2) {
    ctx.fillStyle = '#7a6a5a';
    ctx.font = '9px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(T('hud_hint') || '---', w / 2, h / 2 + 3);
    return;
  }
  const maxPts = Math.min(historySnapshots.length, 30);
  const pts = historySnapshots.slice(-maxPts);
  function plotLine(valGetter, color, minV, maxV) {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    for (let i = 0; i < pts.length; i++) {
      const x = (i / (pts.length - 1)) * (w - 14) + 7;
      const v = valGetter(pts[i]);
      const norm = Math.max(0, Math.min(1, (v - minV) / (maxV - minV || 1)));
      const y = h - 6 - norm * (h - 12);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  plotLine(p => p.hdi, '#84A97C', 0.4, 1.0);
  plotLine(p => p.gini, '#C89B6D', 0.0, 0.6);
  plotLine(p => p.emp, '#6D9BC8', 0.5, 1.0);
}

window.applyI18n = function(map) {
  window.__i18n = map;
  document.documentElement.lang = numLocale();
  document.querySelectorAll('[data-i18n]').forEach(e => { e.textContent = T(e.dataset.i18n); });
  document.querySelectorAll('[data-i18n-term]').forEach(e => {
    const text = T(e.dataset.i18nTerm);
    const cut = text.indexOf(':') + 1;
    const term = document.createElement('b');
    term.textContent = text.slice(0, cut);
    e.replaceChildren(term, document.createTextNode(text.slice(cut)));
  });
  drawHistoryChart();
};

window.updateHud = function(data) {
  setText('v-year', String(data.year));
  setText('v-pop', fmtInt(data.population_size));
  setText('v-drawn', fmtInt(data.citizens_drawn));
  const hasCycle = !!data.latest_cycle;
  const hint = document.getElementById('v-hint');
  if (hint) hint.style.display = hasCycle ? 'none' : '';
  const body = document.getElementById('ev-body');
  if (hasCycle) {
    const c = data.latest_cycle;
    setText('v-hdi', fmtDec(c.aggregate_hdi, 3));
    setText('v-gini', fmtDec(c.aggregate_gini, 3));
    setText('v-emp', fmtDec(c.aggregate_employment * 100, 1) + '%');
    historySnapshots.push({
      year: data.year,
      hdi: c.aggregate_hdi,
      gini: c.aggregate_gini,
      emp: c.aggregate_employment
    });
    body.replaceChildren(...c.events.map(e => {
      const line = document.createElement('div');
      line.className = 'ev-line';
      line.textContent = '[' + e.category + '] ' + e.title;
      return line;
    }));
  } else {
    setText('v-hdi', '—');
    setText('v-gini', '—');
    setText('v-emp', '—');
    historySnapshots.length = 0;
    const idle = document.createElement('div');
    idle.className = 'ev-line';
    idle.style.color = '#7a6a5a';
    idle.textContent = T('ev_idle');
    body.replaceChildren(idle);
  }
  drawHistoryChart();
};

document.getElementById('leg-toggle').addEventListener('click', () => {
  const box = document.getElementById('legend');
  box.classList.toggle('collapsed');
  setText('leg-caret', box.classList.contains('collapsed') ? '\u25b8' : '\u25be');
});
</script>
<script type="importmap">
{"imports":{
  "three":"./assets/js/three.module.min.js",
  "three/addons/":"./assets/js/"
}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const W = () => window.innerWidth, H = () => window.innerHeight;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x16110E);

const camera = new THREE.PerspectiveCamera(52, W() / H(), 0.1, 300);
camera.position.set(4, 26, 38);
camera.lookAt(4, 0, 1);

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(W(), H());
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xF4EAD8, 0.40));
const sun = new THREE.DirectionalLight(0xC89B6D, 1.0);
sun.position.set(8, 18, 10);
scene.add(sun);
const fill = new THREE.DirectionalLight(0x84A97C, 0.28);
fill.position.set(-10, 6, -8);
scene.add(fill);

const CAM_CX = 4, CAM_CZ = 1;

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(CAM_CX, 1, CAM_CZ);
controls.minDistance = 8;
controls.maxDistance = 90;
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.screenSpacePanning = true;
controls.update();

function zoomCamera(factor) {
  const offset = camera.position.clone().sub(controls.target);
  const newLen = Math.max(controls.minDistance,
                          Math.min(controls.maxDistance, offset.length() * factor));
  camera.position.copy(controls.target).addScaledVector(offset.normalize(), newLen);
  controls.update();
}
document.getElementById('zoom-in').addEventListener('click',  () => zoomCamera(0.78));
document.getElementById('zoom-out').addEventListener('click', () => zoomCamera(1.28));

const REGIONS = [
  {id:"BR-SP",name:"São Paulo",      lat:-23.55,lon:-46.63,pop:45000000},
  {id:"BR-RJ",name:"Rio de Janeiro", lat:-22.91,lon:-43.17,pop:17000000},
  {id:"BR-MG",name:"Minas Gerais",   lat:-19.92,lon:-43.94,pop:21000000},
  {id:"BR-BA",name:"Bahia",          lat:-12.97,lon:-38.50,pop:14000000},
  {id:"BR-PR",name:"Paraná",         lat:-25.42,lon:-49.27,pop:11000000},
  {id:"BR-RS",name:"Rio G. do Sul",  lat:-30.03,lon:-51.22,pop:11000000},
  {id:"BR-PE",name:"Pernambuco",     lat: -8.05,lon:-34.90,pop: 9600000},
  {id:"BR-CE",name:"Ceará",          lat: -3.72,lon:-38.54,pop: 9200000},
  {id:"BR-PA",name:"Pará",           lat: -1.46,lon:-48.50,pop: 8700000},
  {id:"BR-AM",name:"Amazonas",       lat: -3.10,lon:-60.02,pop: 4200000},
];
const POP_MAX = 45000000;

function mapXZ(lat, lon) {
  const latMin = -34, latMax = -1, lonMin = -62, lonMax = -34;
  const x = ((lon - lonMin) / (lonMax - lonMin) - 0.5) * 26;
  const z = -((lat - latMin) / (latMax - latMin) - 0.5) * 22;
  return [x, z];
}

function hdiColor(hdi) {
  const lo = new THREE.Color(0xC26653);
  const mid = new THREE.Color(0xC89B6D);
  const hi  = new THREE.Color(0x84A97C);
  const c   = new THREE.Color();
  if (hdi < 0.5) c.lerpColors(lo, mid, hdi * 2);
  else           c.lerpColors(mid, hi, (hdi - 0.5) * 2);
  return c;
}

function makeLabel() {
  const cv = document.createElement('canvas');
  cv.width = 320; cv.height = 96;
  const tex = new THREE.CanvasTexture(cv);
  const mat = new THREE.SpriteMaterial({map: tex, transparent: true, depthTest: false});
  const spr = new THREE.Sprite(mat);
  spr.scale.set(5.5, 1.65, 1);
  return spr;
}

function fmtMillions(n) {
  return Number(n / 1e6).toLocaleString(numLocale(),
    {minimumFractionDigits: 1, maximumFractionDigits: 1}) + 'M';
}

function paintLabel(spr, name, hdi, gini, pop) {
  const ctx = spr.material.map.image.getContext('2d');
  ctx.clearRect(0, 0, 320, 96);
  ctx.fillStyle = 'rgba(22,17,14,0.78)'; ctx.fillRect(0, 0, 320, 96);
  ctx.textAlign = 'center';
  ctx.font = 'bold 22px monospace'; ctx.fillStyle = '#F4EAD8';
  ctx.fillText(name, 160, 28);
  ctx.font = '16px monospace'; ctx.fillStyle = '#C89B6D';
  const hdiText = hdi === null ? '—' : fmtDec(hdi, 3);
  const giniText = gini === null ? '—' : fmtDec(gini, 3);
  ctx.fillText(T('label_hdi') + ' ' + hdiText + ' | ' + T('label_gini') + ' ' + giniText, 160, 54);
  ctx.fillStyle = '#9a8a7a';
  ctx.fillText(T('label_pop') + ' ' + fmtMillions(pop), 160, 78);
  spr.material.map.needsUpdate = true;
}

const ETHNIC_COLS = [
  [0.62,0.40,0.20],[0.76,0.56,0.32],[0.91,0.76,0.62],
  [0.82,0.62,0.36],[0.86,0.72,0.52],
];
const ETHNIC_W = [0.43,0.28,0.21,0.05,0.03];
function pickEthnic() {
  let r = Math.random(), cum = 0;
  for (let i = 0; i < ETHNIC_W.length; i++) {
    cum += ETHNIC_W[i];
    if (r <= cum) return ETHNIC_COLS[i];
  }
  return ETHNIC_COLS[0];
}

const PARTS_PER_REGION = 240;
const cityData = {};
const towerMeshes = [];
const pPositions = [], pColors = [], pPhase = [], pCityX = [], pCityZ = [], pRadius = [];
let activeInspectorRegionId = null;
let latestRegionMetrics = {};
let latestCycleEvents = [];

REGIONS.forEach(r => {
  const [cx, cz] = mapXZ(r.lat, r.lon);
  const hdi = 0.75;
  const towerH = 0.5 + hdi * 5.0;

  const tGeo = new THREE.CylinderGeometry(0.30, 0.50, towerH, 8);
  const tMat = new THREE.MeshLambertMaterial({color: hdiColor(hdi)});
  const tower = new THREE.Mesh(tGeo, tMat);
  tower.position.set(cx, towerH / 2, cz);
  tower.userData = { regionId: r.id };
  towerMeshes.push(tower);
  scene.add(tower);

  const popR = 0.7 + (r.pop / POP_MAX) * 2.2;
  const rGeo = new THREE.RingGeometry(popR, popR + 0.18, 32);
  const rMat = new THREE.MeshBasicMaterial(
    {color: 0xC89B6D, side: THREE.DoubleSide, transparent: true, opacity: 0.55});
  const ring = new THREE.Mesh(rGeo, rMat);
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(cx, 0.02, cz);
  scene.add(ring);

  const label = makeLabel();
  paintLabel(label, r.name, null, null, r.pop);
  label.position.set(cx, towerH + 2.2, cz);
  scene.add(label);

  cityData[r.id] = {tower, tMat, label, ring, rMat, cx, cz, towerH, popR};

  for (let i = 0; i < PARTS_PER_REGION; i++) {
    const angle = Math.random() * Math.PI * 2;
    const rad   = popR + 0.3 + Math.random() * 1.6;
    pPositions.push(cx, Math.random() * 2.5 + 0.3, cz);
    const [cr, cg, cb] = pickEthnic();
    pColors.push(cr, cg, cb);
    pPhase.push(angle);
    pCityX.push(cx);
    pCityZ.push(cz);
    pRadius.push(rad);
  }
});

const pCount = pPositions.length / 3;
const pGeo   = new THREE.BufferGeometry();
const pPos   = new Float32Array(pPositions);
const pCol   = new Float32Array(pColors);
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color',    new THREE.BufferAttribute(pCol, 3));
const pMat = new THREE.PointsMaterial(
  {size: 0.13, vertexColors: true, transparent: true, opacity: 0.82});
scene.add(new THREE.Points(pGeo, pMat));

const groundGeo = new THREE.PlaneGeometry(40, 36);
const groundMat = new THREE.MeshBasicMaterial({color: 0x1c1410, side: THREE.DoubleSide});
const ground    = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.set(4, -0.01, 1);
scene.add(ground);

const grid = new THREE.GridHelper(42, 42, 0x2a1e14, 0x221810);
grid.position.set(4, 0, 1);
scene.add(grid);

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function showInspector(regId) {
  activeInspectorRegionId = regId;
  const rMeta = REGIONS.find(x => x.id === regId);
  if (!rMeta) return;
  const rData = latestRegionMetrics[regId] || {
    hdi: 0.75, gini: 0.35, population_size: rMeta.pop,
    active_workforce: Math.round(rMeta.pop * 0.65)
  };
  const p = document.getElementById('inspector');
  if (!p) return;
  setText('ins-name', rMeta.name);
  setText('ins-id', regId);
  setText('ins-hdi', fmtDec(rData.hdi, 3));
  setText('ins-gini', fmtDec(rData.gini, 3));
  setText('ins-pop', fmtInt(rData.population_size));
  setText('ins-work', fmtInt(rData.active_workforce));
  const evContainer = document.getElementById('ins-events');
  const localEvs = latestCycleEvents.filter(e => e.affected_region_ids && e.affected_region_ids.includes(regId));
  if (localEvs.length > 0) {
    evContainer.replaceChildren(...localEvs.map(e => {
      const div = document.createElement('div');
      div.className = 'ins-ev-line';
      div.textContent = '[' + e.category + '] ' + e.title;
      return div;
    }));
  } else {
    const div = document.createElement('div');
    div.className = 'ins-ev-line';
    div.style.color = '#7a6a5a';
    div.textContent = T('inspector_no_events');
    evContainer.replaceChildren(div);
  }
  p.style.display = 'block';
}

document.getElementById('ins-close').addEventListener('click', () => {
  activeInspectorRegionId = null;
  const p = document.getElementById('inspector');
  if (p) p.style.display = 'none';
});

renderer.domElement.addEventListener('click', (evt) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((evt.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((evt.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(towerMeshes, false);
  if (hits.length > 0) {
    const regId = hits[0].object.userData.regionId;
    showInspector(regId);
  }
});

window.updateSimulation = function(data) {
  if (!data.regions) return;
  if (data.latest_cycle) {
    latestCycleEvents = data.latest_cycle.events || [];
  } else {
    latestCycleEvents = [];
  }
  data.regions.forEach(r => {
    latestRegionMetrics[r.region_id] = r;
    const d = cityData[r.region_id];
    if (!d) return;
    const hdi  = r.hdi ?? 0.7;
    const newH = 0.5 + hdi * 5.0;
    d.tower.scale.y    = newH / d.towerH;
    d.tower.position.y = newH / 2;
    d.tMat.color.copy(hdiColor(hdi));
    d.label.position.y = newH + 2.2;
    paintLabel(d.label, REGIONS.find(x => x.id === r.region_id).name,
               hdi, r.gini, r.population_size);
  });
  if (activeInspectorRegionId) {
    showInspector(activeInspectorRegionId);
  }
};

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  if (!prefersReducedMotion) {
    const pos = pGeo.attributes.position.array;
    for (let i = 0; i < pCount; i++) {
      pPhase[i]  += 0.004 + (i % 5) * 0.0006;
      pos[i * 3]     = pCityX[i] + Math.cos(pPhase[i]) * pRadius[i];
      pos[i * 3 + 2] = pCityZ[i] + Math.sin(pPhase[i]) * pRadius[i];
    }
    pGeo.attributes.position.needsUpdate = true;
  }
  renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
  camera.aspect = W() / H();
  camera.updateProjectionMatrix();
  renderer.setSize(W(), H());
});

animate();
</script>
</body>
</html>"""


def _create_render_widget(html_content: str) -> tuple[QWidget, bool]:
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView

        view = QWebEngineView()
        base_url = QUrl.fromLocalFile(str(Path(__file__).resolve().parent) + "/")
        view.setHtml(html_content, baseUrl=base_url)
        return view, True
    except Exception:
        lbl = QLabel(_WEBENGINE_UNAVAILABLE_MESSAGE)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl, False


class SimulationTab(QWidget):
    def __init__(
        self, parent: QWidget | None = None, translator: LocalizationCatalog | None = None
    ) -> None:
        super().__init__(parent)
        self._sim_engine = NationSimulationEngine()
        self._event_matrix = StochasticEventMatrix(seed=42)
        self._advance_text = ""
        self._status_texts: dict[str, str] = {}
        self._viewer_texts: dict[str, str] = {}
        self._number_locale = QLocale()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        self.grp_controls = QGroupBox()
        ctl_layout = QVBoxLayout(self.grp_controls)
        ctl_layout.setSpacing(3)

        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.lbl_status_year = QLabel()
        self.lbl_status_year.setObjectName("SectionHeading")
        yr_pol = self.lbl_status_year.sizePolicy()
        yr_pol.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
        self.lbl_status_year.setSizePolicy(yr_pol)
        status_row.addWidget(self.lbl_status_year, stretch=1)

        self.btn_advance_year = QPushButton()
        self.btn_advance_year.setObjectName("PrimaryActionButton")
        self.btn_advance_year.clicked.connect(self._on_advance_year)
        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self._on_reset)
        status_row.addWidget(self.btn_advance_year)
        status_row.addWidget(self.btn_reset)
        ctl_layout.addLayout(status_row)

        step_row = QHBoxLayout()
        step_row.setSpacing(6)
        self.lbl_years_step = QLabel()
        self.spn_years_step = QSpinBox()
        self.spn_years_step.setRange(1, YEARS_PER_STEP_LIMIT)
        self.spn_years_step.valueChanged.connect(self._on_years_step_changed)
        step_row.addWidget(self.lbl_years_step)
        step_row.addWidget(self.spn_years_step)

        self.lbl_scenario = QLabel()
        self.cmb_scenario = QComboBox()
        for scenario in SimulationScenario:
            self.cmb_scenario.addItem(scenario.name, scenario)
        self.cmb_scenario.currentIndexChanged.connect(self._on_scenario_changed)
        step_row.addWidget(self.lbl_scenario)
        step_row.addWidget(self.cmb_scenario)
        step_row.addStretch(1)
        ctl_layout.addLayout(step_row)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)
        self.btn_export_csv = QPushButton()
        self.btn_export_csv.clicked.connect(self._on_export_csv)
        self.btn_export_json = QPushButton()
        self.btn_export_json.clicked.connect(self._on_export_json)
        actions_row.addWidget(self.btn_export_csv)
        actions_row.addWidget(self.btn_export_json)
        actions_row.addStretch(1)
        ctl_layout.addLayout(actions_row)

        self.lbl_status_metrics = QLabel()
        self.lbl_status_metrics.setWordWrap(True)
        self.lbl_status_metrics.setMinimumWidth(0)
        ctl_layout.addWidget(self.lbl_status_metrics)

        outer.addWidget(self.grp_controls)

        self.grp_events = QGroupBox()
        evt_layout = QVBoxLayout(self.grp_events)
        evt_layout.setSpacing(2)
        self.lbl_events = QLabel()
        self.lbl_events.setWordWrap(True)
        evt_layout.addWidget(self.lbl_events)
        outer.addWidget(self.grp_events)

        self._render_widget: Any
        self._render_widget, self._has_webengine = _create_render_widget(_THREE_JS_HTML)
        outer.addWidget(self._render_widget, stretch=1)
        if self._has_webengine:
            self._render_widget.loadFinished.connect(self._on_page_loaded)

        self.apply_translations(translator or LocalizationCatalog())

    def apply_translations(self, translator: LocalizationCatalog) -> None:
        self._status_texts = {
            key: translator.translate(f"simulation.{key}") for key in STATUS_TEXT_KEYS
        }
        self._viewer_texts = {
            key: translator.translate(f"simulation.viewer.{key}") for key in VIEWER_TEXT_KEYS
        }
        self._number_locale = QLocale(self._viewer_texts["number_locale"])
        self.lbl_years_step.setText(self._status_texts["years_step_label"])
        self.lbl_scenario.setText(self._status_texts["scenario_label"])
        self.btn_export_csv.setText(self._status_texts["btn_export_csv"])
        self.btn_export_json.setText(self._status_texts["btn_export_json"])
        current_idx = self.cmb_scenario.currentIndex()
        self.cmb_scenario.blockSignals(True)
        self.cmb_scenario.clear()
        for scenario in SimulationScenario:
            self.cmb_scenario.addItem(
                translator.translate(f"simulation.scenario.{scenario.name}"),
                scenario,
            )
        if 0 <= current_idx < self.cmb_scenario.count():
            self.cmb_scenario.setCurrentIndex(current_idx)
        else:
            self.cmb_scenario.setCurrentIndex(0)
        self.cmb_scenario.blockSignals(False)
        self._refresh_advance_button()
        self._push_viewer_texts()
        self._refresh_status()
        self._refresh_events()

    def set_group_titles(self, controls_title: str, events_title: str) -> None:
        self.grp_controls.setTitle(controls_title)
        self.grp_events.setTitle(events_title)

    def set_button_texts(self, advance_text: str, reset_text: str) -> None:
        self._advance_text = advance_text
        self.btn_reset.setText(reset_text)
        self._refresh_advance_button()

    def set_active_macro_directive(self, directive: str) -> None:
        self._sim_engine.set_active_macro_directive(directive)

    def _refresh_advance_button(self) -> None:
        years = self.spn_years_step.value()
        if years == 1 or not self._advance_text:
            self.btn_advance_year.setText(self._advance_text)
            return
        self.btn_advance_year.setText(self._status_texts["btn_advance_years"].format(years=years))

    def _on_years_step_changed(self, _years: int) -> None:
        self._refresh_advance_button()

    def _on_scenario_changed(self, index: int) -> None:
        raw = self.cmb_scenario.itemData(index)
        try:
            self._sim_engine.scenario = SimulationScenario(raw)
        except (ValueError, KeyError):
            pass

    def _on_export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._status_texts.get("btn_export_csv", "Export CSV"),
            "cibersoc_simulation.csv",
            "CSV Files (*.csv)",
        )
        if file_path:
            self._sim_engine.export_time_series_csv(Path(file_path))

    def _on_export_json(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self._status_texts.get("btn_export_json", "Export JSON"),
            "cibersoc_simulation.json",
            "JSON Files (*.json)",
        )
        if file_path:
            self._sim_engine.export_time_series_json(Path(file_path))

    def _on_page_loaded(self, loaded: bool) -> None:
        if loaded:
            self._push_viewer_texts()
            self._refresh_status()

    def _push_viewer_texts(self) -> None:
        if not self._has_webengine:
            return
        self._render_widget.page().runJavaScript(
            "if(window.applyI18n){applyI18n(" + json.dumps(self._viewer_texts) + ");}"
        )

    def _push_simulation_data(self, json_payload: str) -> None:
        if not self._has_webengine:
            return
        self._render_widget.page().runJavaScript(
            "(function(d){if(window.updateHud){updateHud(d);}"
            "if(window.updateSimulation){updateSimulation(d);}})(" + json_payload + ");"
        )

    def _refresh_status(self) -> None:
        engine = self._sim_engine
        formatter = self._number_locale
        self.lbl_status_year.setText(
            self._status_texts["status_year"].format(
                year=engine.current_year,
                population=formatter.toString(engine.total_population),
                drawn=formatter.toString(engine.citizens_drawn),
            )
        )
        if engine.cycles:
            last = engine.cycles[-1]
            self.lbl_status_metrics.setText(
                self._status_texts["status_metrics"].format(
                    hdi=formatter.toString(last.aggregate_hdi, "f", 3),
                    gini=formatter.toString(last.aggregate_gini, "f", 3),
                    employment=formatter.toString(last.aggregate_employment * 100, "f", 1),
                )
            )
        else:
            self.lbl_status_metrics.setText(self._status_texts["status_idle"])
        self._push_simulation_data(json.dumps(engine.serialise_for_renderer()))

    def _refresh_events(self) -> None:
        if not self._sim_engine.cycles:
            self.lbl_events.setText(self._status_texts["events_idle"])
            return
        last = self._sim_engine.cycles[-1]
        lines = [
            f"[{e.category}]  {e.title}"
            f"  (severity={e.severity:.2f}, Δgdp={e.gdp_delta:+.2f}, Δwelfare={e.welfare_delta:+.2f})"
            for e in last.events
        ]
        self.lbl_events.setText("\n".join(lines))

    def _on_advance_year(self) -> None:
        for _ in range(self.spn_years_step.value()):
            self._sim_engine.advance_year(self._event_matrix)
        self._refresh_status()
        self._refresh_events()

    def _on_reset(self) -> None:
        raw = self.cmb_scenario.currentData()
        try:
            target_scenario = SimulationScenario(raw)
        except (ValueError, KeyError):
            target_scenario = SimulationScenario.BASELINE
        self._sim_engine = NationSimulationEngine(scenario=target_scenario)
        self._refresh_status()
        self._refresh_events()
