from __future__ import annotations

from collections.abc import Callable
import importlib
import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QLocale, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..i18n.translator import LocalizationCatalog
from ..simulation.engine import (
    InstitutionalRegime,
    NationSimulationEngine,
    SimulationScenario,
    StochasticEventMatrix,
)

YEARS_PER_STEP_LIMIT: int = 1000

STATUS_TEXT_KEYS: tuple[str, ...] = (
    "status_year",
    "status_idle",
    "status_metrics",
    "status_comparison",
    "events_idle",
    "years_step_label",
    "btn_advance_years",
    "scenario_label",
    "regime_label",
    "btn_export_csv",
    "btn_export_json",
)

VIEWER_TEXT_KEYS: tuple[str, ...] = (
    "number_locale",
    "title",
    "ctrl_hint",
    "hud_cycle",
    "hud_year",
    "hud_regime",
    "hud_reg_dem",
    "hud_reg_oli",
    "hud_reg_cen",
    "hud_population",
    "hud_citizens",
    "hud_metrics",
    "hud_hdi",
    "hud_gini",
    "hud_employment",
    "hud_comparison",
    "hud_comparison_tip",
    "hud_hint",
    "hud_history",
    "hud_history_key",
    "legend_title",
    "legend_towers_title",
    "legend_towers_text",
    "legend_scale_low",
    "legend_scale_high",
    "legend_rings_title",
    "legend_rings_text",
    "legend_arcs_title",
    "legend_arcs_text",
    "legend_particles_title",
    "legend_particles_text",
    "glossary_title",
    "gl_comparison",
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
body > canvas { display: block; position: absolute; top: 0; left: 0; }

#hud {
  position: absolute; top: 10px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.94); border: 1px solid #4A3930;
  padding: 6px 10px; border-radius: 4px;
  width: clamp(215px, 26vw, 315px);
}
#hud .section { font-size: clamp(7px,0.75vw,8.5px); color: #9a8a7a;
                letter-spacing: 0.9px; margin-bottom: 2px; margin-top: 5px; }
#hud .section:first-child { margin-top: 0; }
#hud .score-hdr { border-top: 1px dashed #3a2e24; padding-top: 4px; cursor: help; color: #C89B6D; }
#hud .row { font-size: clamp(8px,0.88vw,10.5px); color: #C89B6D;
            margin-bottom: 1px; display: flex;
            justify-content: space-between; gap: 8px; }
#hud .score-row { padding: 1px 4px; border-radius: 2px; border-left: 2px solid transparent; }
#hud .score-row.active-reg { background: rgba(200,155,109,0.14); border-left-color: #F4EAD8; }
#hud .score-row.dem-row { color: #84A97C; }
#hud .score-row.dem-row .val { color: #9EC996; }
#hud .score-row.cen-row { color: #C89B6D; }
#hud .score-row.oli-row { color: #C26653; }
#hud .score-row.oli-row .val { color: #D98270; }
#hud .val  { color: #F4EAD8; font-weight: bold; white-space: nowrap; }
#hud .comp-note { font-size: clamp(7px,0.72vw,9px); color: #9a8a7a;
                  line-height: 1.2; margin: 1px 0 2px 0; }
#history-chart {
  display: block; width: 100%; height: 34px;
  margin-top: 2px; border: 1px solid #3a2e24;
  border-radius: 2px; background: #120d0a;
}

#inspector {
  position: absolute; top: 46px; right: 54px; z-index: 12;
  background: rgba(22,17,14,0.95); border: 1px solid #C89B6D;
  padding: 10px 14px; border-radius: 4px;
  width: clamp(210px, 26vw, 340px); max-height: calc(100vh - 60px); overflow-y: auto;
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
  position: absolute; top: 10px; right: 54px; z-index: 11;
  background: rgba(22,17,14,0.94); border: 1px solid #6E523E;
  padding: 7px 12px; border-radius: 4px;
  width: clamp(220px, 27vw, 355px); max-height: calc(100vh - 54px);
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
#legend .sw-arc { width: 22px; height: 9px; border-top: 2px solid #DFB589;
                  border-radius: 50% 50% 0 0; flex-shrink: 0; }
#legend .sw-dots { display: inline-flex; gap: 3px; flex-shrink: 0; }
#legend .sw-dots i { width: 5px; height: 5px; border-radius: 50%; display: inline-block; }
#legend .gloss { border-top: 1px solid #3a2e24; padding-top: 7px; }
#legend .gloss-hdr { font-size: clamp(7px,0.85vw,10px); color: #C89B6D;
                     letter-spacing: 1px; margin-bottom: 5px; }
#legend .gl-item { font-size: clamp(7px,0.85vw,11px); line-height: 1.4;
                   color: #9a8a7a; margin-bottom: 5px; }
#legend .gl-item b { color: #C89B6D; }

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
  <div class="row"><span data-i18n="hud_regime"></span><span class="val" id="v-regime">A · DEM</span></div>
  <div class="row"><span data-i18n="hud_population"></span><span class="val" id="v-pop">—</span></div>
  <div class="row"><span data-i18n="hud_citizens"></span><span class="val" id="v-drawn">0</span></div>
  <div class="section" data-i18n="hud_metrics"></div>
  <div class="row"><span data-i18n="hud_hdi"></span><span class="val" id="v-hdi">—</span></div>
  <div class="row"><span data-i18n="hud_gini"></span><span class="val" id="v-gini">—</span></div>
  <div class="row"><span data-i18n="hud_employment"></span><span class="val" id="v-emp">—</span></div>
  <div class="section score-hdr" data-i18n-title="hud_comparison_tip" data-i18n="hud_comparison"></div>
  <div class="row score-row dem-row" id="sr-dem"><span data-i18n="hud_reg_dem"></span><span class="val" id="v-sc-dem">—</span></div>
  <div class="row score-row cen-row" id="sr-cen"><span data-i18n="hud_reg_cen"></span><span class="val" id="v-sc-cen">—</span></div>
  <div class="row score-row oli-row" id="sr-oli"><span data-i18n="hud_reg_oli"></span><span class="val" id="v-sc-oli">—</span></div>
  <div class="section" data-i18n="hud_history"></div>
  <div class="comp-note" data-i18n="hud_history_key"></div>
  <canvas id="history-chart" width="256" height="38"></canvas>
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
      <div class="leg-title"><span class="sw-arc"></span><span data-i18n="legend_arcs_title"></span></div>
      <div class="leg-text" data-i18n="legend_arcs_text"></div>
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
      <div class="gl-item" data-i18n-term="gl_comparison"></div>
      <div class="gl-item" data-i18n-term="gl_population"></div>
      <div class="gl-item" data-i18n-term="gl_citizens"></div>
      <div class="gl-item" data-i18n-term="gl_hdi"></div>
      <div class="gl-item" data-i18n-term="gl_gini"></div>
      <div class="gl-item" data-i18n-term="gl_employment"></div>
    </div>
  </div>
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
  document.querySelectorAll('[data-i18n-title]').forEach(e => { e.title = T(e.dataset.i18nTitle); });
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
  const regMap = {
    'CIBERSOC_DEMARCHY': T('hud_reg_dem') || 'A · Sortition + 1/N',
    'ELECTORAL_OLIGARCHY': T('hud_reg_oli') || 'B · Elections + CEOs',
    'BUREAUCRATIC_CENTRALISM': T('hud_reg_cen') || 'C · State Bureaucracy'
  };
  setText('v-regime', regMap[data.regime] || regMap['CIBERSOC_DEMARCHY']);
  setText('v-pop', fmtInt(data.population_size));
  setText('v-drawn', fmtInt(data.citizens_drawn));
  const rowIds = {
    'CIBERSOC_DEMARCHY': 'sr-dem',
    'BUREAUCRATIC_CENTRALISM': 'sr-cen',
    'ELECTORAL_OLIGARCHY': 'sr-oli'
  };
  Object.entries(rowIds).forEach(([k, id]) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('active-reg', data.regime === k);
  });
  const hasCycle = !!data.latest_cycle;
  if (hasCycle) {
    const c = data.latest_cycle;
    setText('v-hdi', fmtDec(c.aggregate_hdi, 3));
    setText('v-gini', fmtDec(c.aggregate_gini, 3));
    setText('v-emp', fmtDec(c.aggregate_employment * 100, 1) + '%');
    if (data.regime_comparison) {
      const rc = data.regime_comparison;
      if (rc.CIBERSOC_DEMARCHY) {
        setText('v-sc-dem', fmtDec(rc.CIBERSOC_DEMARCHY.aggregate_hdi, 3) + ' · ' + fmtDec(rc.CIBERSOC_DEMARCHY.aggregate_gini, 3));
      }
      if (rc.BUREAUCRATIC_CENTRALISM) {
        setText('v-sc-cen', fmtDec(rc.BUREAUCRATIC_CENTRALISM.aggregate_hdi, 3) + ' · ' + fmtDec(rc.BUREAUCRATIC_CENTRALISM.aggregate_gini, 3));
      }
      if (rc.ELECTORAL_OLIGARCHY) {
        setText('v-sc-oli', fmtDec(rc.ELECTORAL_OLIGARCHY.aggregate_hdi, 3) + ' · ' + fmtDec(rc.ELECTORAL_OLIGARCHY.aggregate_gini, 3));
      }
    }
    historySnapshots.push({
      year: data.year,
      hdi: c.aggregate_hdi,
      gini: c.aggregate_gini,
      emp: c.aggregate_employment
    });
  } else {
    setText('v-hdi', '—');
    setText('v-gini', '—');
    setText('v-emp', '—');
    setText('v-sc-dem', '—');
    setText('v-sc-cen', '—');
    setText('v-sc-oli', '—');
    historySnapshots.length = 0;
  }
  drawHistoryChart();
};

document.getElementById('leg-toggle').addEventListener('click', () => {
  const box = document.getElementById('legend');
  box.classList.toggle('collapsed');
  setText('leg-caret', box.classList.contains('collapsed') ? '\u25b8' : '\u25be');
});
if (window.innerHeight < 520) {
  const box = document.getElementById('legend');
  box.classList.add('collapsed');
  setText('leg-caret', '\u25b8');
}
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

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: true });
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
window.zoomScene = zoomCamera;
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
  const latMin = -34, latMax = 5.5, lonMin = -74, lonMax = -34;
  const x = ((lon - lonMin) / (lonMax - lonMin) - 0.5) * 30;
  const z = -((lat - latMin) / (latMax - latMin) - 0.5) * 26;
  return [x, z];
}

const BRAZIL_OUTLINE = [
  [5.27,-60.20],[4.40,-51.55],[1.80,-49.90],[-0.80,-48.20],[-2.55,-44.30],
  [-2.90,-40.80],[-3.72,-38.50],[-5.10,-35.20],[-8.05,-34.80],[-10.90,-37.05],
  [-12.97,-38.50],[-16.40,-39.05],[-20.30,-40.30],[-22.90,-42.00],[-23.00,-43.20],
  [-24.00,-46.30],[-25.50,-48.50],[-27.60,-48.55],[-30.05,-50.20],[-33.75,-53.40],
  [-30.90,-55.55],[-29.75,-57.10],[-25.60,-54.60],[-24.05,-54.30],[-22.10,-58.00],
  [-19.00,-57.65],[-16.30,-58.40],[-13.50,-60.40],[-10.95,-65.35],[-11.00,-69.60],
  [-9.50,-72.80],[-7.50,-73.98],[-4.20,-69.95],[-1.20,-69.45],[1.70,-67.10],
  [3.90,-64.20]
];

const MACRO_BORDERS = [
  [[-9.50,-72.80],[-8.80,-63.90],[-9.80,-56.00],[-10.20,-48.30],[-2.55,-44.30]],
  [[-10.20,-48.30],[-14.20,-46.20],[-18.30,-39.65]],
  [[-14.20,-46.20],[-19.95,-51.00],[-24.05,-54.30]],
  [[-24.05,-54.30],[-22.95,-49.95],[-25.20,-48.10]]
];

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

const groundGeo = new THREE.PlaneGeometry(44, 40);
const groundMat = new THREE.MeshBasicMaterial({color: 0x18120e, side: THREE.DoubleSide});
const ground    = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.set(2, -0.02, 0);
scene.add(ground);

const grid = new THREE.GridHelper(44, 44, 0x2a1e14, 0x201710);
grid.position.set(2, -0.01, 0);
scene.add(grid);

(function buildBrazilMap() {
  const shape = new THREE.Shape();
  const outlinePts3D = [];
  BRAZIL_OUTLINE.forEach(([lat, lon], idx) => {
    const [bx, bz] = mapXZ(lat, lon);
    if (idx === 0) shape.moveTo(bx, -bz);
    else shape.lineTo(bx, -bz);
    outlinePts3D.push(new THREE.Vector3(bx, 0.025, bz));
  });
  shape.closePath();
  const landGeo = new THREE.ShapeGeometry(shape);
  const landMat = new THREE.MeshLambertMaterial({
    color: 0x281D15,
    emissive: 0x140E0A,
    side: THREE.DoubleSide
  });
  const landMesh = new THREE.Mesh(landGeo, landMat);
  landMesh.rotation.x = -Math.PI / 2;
  landMesh.position.y = 0.01;
  scene.add(landMesh);

  const borderGeo = new THREE.BufferGeometry().setFromPoints(outlinePts3D);
  const borderMat = new THREE.LineBasicMaterial({
    color: 0xC89B6D,
    transparent: true,
    opacity: 0.78
  });
  scene.add(new THREE.LineLoop(borderGeo, borderMat));

  const subBorderMat = new THREE.LineBasicMaterial({
    color: 0x6E523E,
    transparent: true,
    opacity: 0.52
  });
  MACRO_BORDERS.forEach(poly => {
    const pts = poly.map(([lat, lon]) => {
      const [px, pz] = mapXZ(lat, lon);
      return new THREE.Vector3(px, 0.022, pz);
    });
    const g = new THREE.BufferGeometry().setFromPoints(pts);
    scene.add(new THREE.Line(g, subBorderMat));
  });
})();

const corridorGroup = new THREE.Group();
scene.add(corridorGroup);

const DEFAULT_CORRIDORS = [
  {from_id:"BR-SP",to_id:"BR-RJ",intensity:0.82},
  {from_id:"BR-SP",to_id:"BR-MG",intensity:0.78},
  {from_id:"BR-SP",to_id:"BR-PR",intensity:0.80},
  {from_id:"BR-PR",to_id:"BR-RS",intensity:0.76},
  {from_id:"BR-MG",to_id:"BR-BA",intensity:0.70},
  {from_id:"BR-BA",to_id:"BR-PE",intensity:0.68},
  {from_id:"BR-PE",to_id:"BR-CE",intensity:0.66},
  {from_id:"BR-CE",to_id:"BR-PA",intensity:0.62},
  {from_id:"BR-PA",to_id:"BR-AM",intensity:0.60},
  {from_id:"BR-SP",to_id:"BR-PA",intensity:0.64}
];

function rebuildCorridors(flows) {
  while (corridorGroup.children.length > 0) {
    const ch = corridorGroup.children.pop();
    if (ch.geometry) ch.geometry.dispose();
    if (ch.material) ch.material.dispose();
  }
  const activeFlows = (flows && flows.length) ? flows : DEFAULT_CORRIDORS;
  const loCol = new THREE.Color(0x8A6543);
  const hiCol = new THREE.Color(0xDFB589);
  activeFlows.forEach(f => {
    const s = cityData[f.from_id];
    const t = cityData[f.to_id];
    if (!s || !t) return;
    const dx = t.cx - s.cx, dz = t.cz - s.cz;
    const dist = Math.hypot(dx, dz);
    const inten = Math.max(0.15, Math.min(1.0, f.intensity || 0.65));
    const arcH = 1.4 + dist * 0.16 + inten * 1.4;
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(s.cx, 0.45, s.cz),
      new THREE.Vector3((s.cx + t.cx) * 0.5, arcH, (s.cz + t.cz) * 0.5),
      new THREE.Vector3(t.cx, 0.45, t.cz)
    );
    const pts = curve.getPoints(28);
    const geo = new THREE.BufferGeometry().setFromPoints(pts);
    const col = new THREE.Color().lerpColors(loCol, hiCol, inten);
    const mat = new THREE.LineBasicMaterial({
      color: col,
      transparent: true,
      opacity: 0.28 + inten * 0.54
    });
    corridorGroup.add(new THREE.Line(geo, mat));
  });
}
rebuildCorridors(DEFAULT_CORRIDORS);

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
  const legBox = document.getElementById('legend');
  if (legBox && !legBox.classList.contains('collapsed')) {
    legBox.classList.add('collapsed');
    setText('leg-caret', '\u25b8');
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
  if (data.inter_regional_flows) {
    rebuildCorridors(data.inter_regional_flows);
  }
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


def _load_default_webengine_cls(
    module_name: str = "PySide6.QtWebEngineWidgets",
    class_name: str = "QWebEngineView",
) -> Callable[[], Any]:
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _create_render_widget(
    html_content: str,
    webengine_view_cls: Callable[[], Any] | None = None,
    module_loader: Callable[[], Callable[[], Any]] = _load_default_webengine_cls,
    allow_offscreen_webengine: bool = False,
) -> tuple[QWidget, bool]:
    is_offscreen = QGuiApplication.platformName().strip().lower() in {"offscreen", "minimal"}
    try:
        if webengine_view_cls is None:
            if is_offscreen and not allow_offscreen_webengine:
                raise RuntimeError("Offscreen platform uses lightweight fallback widget.")
            view_cls = module_loader()
        else:
            view_cls = webengine_view_cls
        view = view_cls()
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
        self,
        parent: QWidget | None = None,
        translator: LocalizationCatalog | None = None,
        render_widget_factory: Callable[[str], tuple[QWidget, bool]] | None = None,
        save_file_dialog: Callable[..., tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(parent)
        self._sim_engine = NationSimulationEngine()
        self._event_matrix = StochasticEventMatrix(seed=42)
        self._save_file_dialog = save_file_dialog or QFileDialog.getSaveFileName
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

        self.status_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.status_row.setSpacing(6)
        self.lbl_status_year = QLabel()
        self.lbl_status_year.setObjectName("SectionHeading")
        yr_pol = self.lbl_status_year.sizePolicy()
        yr_pol.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
        self.lbl_status_year.setSizePolicy(yr_pol)
        self.status_row.addWidget(self.lbl_status_year, stretch=1)

        self.btn_advance_year = QPushButton()
        self.btn_advance_year.setObjectName("PrimaryActionButton")
        self.btn_advance_year.clicked.connect(self._on_advance_year)
        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self._on_reset)
        self.status_row.addWidget(self.btn_advance_year)
        self.status_row.addWidget(self.btn_reset)
        ctl_layout.addLayout(self.status_row)

        self.step_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.step_row.setSpacing(6)
        self.lbl_years_step = QLabel()
        self.spn_years_step = QSpinBox()
        self.spn_years_step.setRange(1, YEARS_PER_STEP_LIMIT)
        self.spn_years_step.valueChanged.connect(self._on_years_step_changed)
        self.step_row.addWidget(self.lbl_years_step)
        self.step_row.addWidget(self.spn_years_step)

        self.lbl_scenario = QLabel()
        self.cmb_scenario = QComboBox()
        self.cmb_scenario.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.cmb_scenario.setMinimumContentsLength(14)
        for scenario in SimulationScenario:
            self.cmb_scenario.addItem(scenario.name, scenario)
        self.cmb_scenario.currentIndexChanged.connect(self._on_scenario_changed)
        self.step_row.addWidget(self.lbl_scenario)
        self.step_row.addWidget(self.cmb_scenario, stretch=1)
        ctl_layout.addLayout(self.step_row)

        self.regime_row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.regime_row.setSpacing(6)
        self.lbl_regime = QLabel()
        self.cmb_regime = QComboBox()
        self.cmb_regime.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.cmb_regime.setMinimumContentsLength(14)
        for regime in InstitutionalRegime:
            self.cmb_regime.addItem(regime.name, regime)
        self.cmb_regime.currentIndexChanged.connect(self._on_regime_changed)
        self.regime_row.addWidget(self.lbl_regime)
        self.regime_row.addWidget(self.cmb_regime, stretch=1)

        self.btn_export_csv = QPushButton()
        self.btn_export_csv.clicked.connect(self._on_export_csv)
        self.btn_export_json = QPushButton()
        self.btn_export_json.clicked.connect(self._on_export_json)
        self.regime_row.addWidget(self.btn_export_csv)
        self.regime_row.addWidget(self.btn_export_json)
        ctl_layout.addLayout(self.regime_row)
        self.adaptive_layouts: tuple[QBoxLayout, ...] = (
            self.status_row,
            self.step_row,
            self.regime_row,
        )

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

        factory = render_widget_factory or _create_render_widget
        self._render_widget: Any
        self._render_widget, self._has_webengine = factory(_THREE_JS_HTML)
        outer.addWidget(self._render_widget, stretch=1)
        if self._has_webengine:
            self._render_widget.setMinimumHeight(310)
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
        self.lbl_regime.setText(self._status_texts["regime_label"])
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

        current_reg_idx = self.cmb_regime.currentIndex()
        self.cmb_regime.blockSignals(True)
        self.cmb_regime.clear()
        for regime in InstitutionalRegime:
            self.cmb_regime.addItem(
                translator.translate(f"simulation.regime.{regime.name}"),
                regime,
            )
        if 0 <= current_reg_idx < self.cmb_regime.count():
            self.cmb_regime.setCurrentIndex(current_reg_idx)
        else:
            self.cmb_regime.setCurrentIndex(0)
        self.cmb_regime.blockSignals(False)

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

    def zoom_in(self) -> None:
        if self._has_webengine:
            self._render_widget.page().runJavaScript("if(window.zoomScene){window.zoomScene(0.78);}")

    def zoom_out(self) -> None:
        if self._has_webengine:
            self._render_widget.page().runJavaScript("if(window.zoomScene){window.zoomScene(1.28);}")

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
            target_scenario = SimulationScenario(raw)
        except (ValueError, KeyError):
            return
        if not self._sim_engine.cycles:
            active_directive = self._sim_engine.active_macro_directive
            self._sim_engine = NationSimulationEngine(
                scenario=target_scenario,
                regime=self._sim_engine.regime,
            )
            if active_directive:
                self._sim_engine.set_active_macro_directive(active_directive)
            self._refresh_status()
        else:
            self._sim_engine.scenario = target_scenario

    def _on_regime_changed(self, index: int) -> None:
        raw = self.cmb_regime.itemData(index)
        try:
            target_regime = InstitutionalRegime(raw)
        except (ValueError, KeyError):
            return
        self._sim_engine.switch_regime(target_regime)
        self._refresh_status()

    def _on_export_csv(self) -> None:
        file_path, _ = self._save_file_dialog(
            self,
            self._status_texts.get("btn_export_csv", "Export CSV"),
            "cibersoc_simulation.csv",
            "CSV Files (*.csv)",
        )
        if file_path:
            self._sim_engine.export_time_series_csv(Path(file_path))

    def _on_export_json(self) -> None:
        file_path, _ = self._save_file_dialog(
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
            metrics_line = self._status_texts["status_metrics"].format(
                hdi=formatter.toString(last.aggregate_hdi, "f", 3),
                gini=formatter.toString(last.aggregate_gini, "f", 3),
                employment=formatter.toString(last.aggregate_employment * 100, "f", 1),
            )
            comp = engine.compare_regimes()
            dem = comp[InstitutionalRegime.CIBERSOC_DEMARCHY.value]
            cen = comp[InstitutionalRegime.BUREAUCRATIC_CENTRALISM.value]
            oli = comp[InstitutionalRegime.ELECTORAL_OLIGARCHY.value]
            comp_line = self._status_texts["status_comparison"].format(
                dem_hdi=formatter.toString(dem["aggregate_hdi"], "f", 3),
                dem_gini=formatter.toString(dem["aggregate_gini"], "f", 3),
                cen_hdi=formatter.toString(cen["aggregate_hdi"], "f", 3),
                cen_gini=formatter.toString(cen["aggregate_gini"], "f", 3),
                oli_hdi=formatter.toString(oli["aggregate_hdi"], "f", 3),
                oli_gini=formatter.toString(oli["aggregate_gini"], "f", 3),
            )
            self.lbl_status_metrics.setText(f"{metrics_line}\n{comp_line}")
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
        raw_scenario = self.cmb_scenario.currentData()
        try:
            target_scenario = SimulationScenario(raw_scenario)
        except (ValueError, KeyError):
            target_scenario = SimulationScenario.BASELINE
        raw_regime = self.cmb_regime.currentData()
        try:
            target_regime = InstitutionalRegime(raw_regime)
        except (ValueError, KeyError):
            target_regime = InstitutionalRegime.CIBERSOC_DEMARCHY
        active_directive = self._sim_engine.active_macro_directive
        self._sim_engine = NationSimulationEngine(
            scenario=target_scenario,
            regime=target_regime,
        )
        if active_directive:
            self._sim_engine.set_active_macro_directive(active_directive)
        self._refresh_status()
        self._refresh_events()
