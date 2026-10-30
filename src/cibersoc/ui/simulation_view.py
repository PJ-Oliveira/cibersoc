from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..simulation.engine import NationSimulationEngine, StochasticEventMatrix

_WEBENGINE_UNAVAILABLE_MESSAGE = (
    "3D visualisation requires the PySide6-WebEngine module.\n"
    "The simulation engine is active — advance years to see Python-side metrics."
)

_THREE_JS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #16110E; color: #F4EAD8; font-family: monospace; overflow: hidden; width: 100vw; height: 100vh; }
canvas { display: block; position: absolute; top: 0; left: 0; }
#overlay {
  position: absolute; top: 12px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.82); border: 1px solid #3a2e24;
  padding: 10px 14px; border-radius: 4px; min-width: 180px;
}
#overlay .metric { font-size: 12px; color: #C89B6D; margin-bottom: 4px; }
#overlay .val { color: #F4EAD8; font-weight: bold; }
#overlay .hint { font-size: 11px; color: #7a6a5a; margin-top: 4px; }
#title-bar {
  position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
  z-index: 10; color: #C89B6D; font-size: 13px; letter-spacing: 2px;
  text-transform: uppercase; pointer-events: none;
}
</style>
</head>
<body>
<div id="title-bar">CIBERSOC Nation Simulation — SEEM Engine</div>
<div id="overlay">
  <div class="metric">Year <span class="val" id="v-year">1 / 10</span></div>
  <div class="metric">Citizens <span class="val" id="v-pop">1,000,000</span></div>
  <div class="metric">HDI <span class="val" id="v-hdi">—</span></div>
  <div class="metric">GINI <span class="val" id="v-gini">—</span></div>
  <div class="metric">Employment <span class="val" id="v-emp">—</span></div>
  <div class="hint" id="v-hint">Advance year to begin simulation</div>
</div>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.min.js"}}
</script>
<script type="module">
import * as THREE from 'three';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x16110E);
scene.fog = new THREE.Fog(0x16110E, 30, 70);

const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
camera.position.set(0, 18, 28);
camera.lookAt(0, 2, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);

const ambient = new THREE.AmbientLight(0xF4EAD8, 0.35);
scene.add(ambient);
const sun = new THREE.DirectionalLight(0xC89B6D, 0.9);
sun.position.set(6, 12, 8);
scene.add(sun);
const fill = new THREE.DirectionalLight(0x84A97C, 0.3);
fill.position.set(-8, 4, -6);
scene.add(fill);

const REGIONS = [
  { id:"BR-SP", name:"São Paulo",         lat:-23.55, lon:-46.63, pop:45000000 },
  { id:"BR-RJ", name:"Rio de Janeiro",    lat:-22.91, lon:-43.17, pop:17000000 },
  { id:"BR-MG", name:"Minas Gerais",      lat:-19.92, lon:-43.94, pop:21000000 },
  { id:"BR-BA", name:"Bahia",             lat:-12.97, lon:-38.50, pop:14000000 },
  { id:"BR-PR", name:"Paraná",            lat:-25.42, lon:-49.27, pop:11000000 },
  { id:"BR-RS", name:"Rio Grande do Sul", lat:-30.03, lon:-51.22, pop:11000000 },
  { id:"BR-PE", name:"Pernambuco",        lat: -8.05, lon:-34.90, pop: 9600000 },
  { id:"BR-CE", name:"Ceará",             lat: -3.72, lon:-38.54, pop: 9200000 },
  { id:"BR-PA", name:"Pará",              lat: -1.46, lon:-48.50, pop: 8700000 },
  { id:"BR-AM", name:"Amazonas",          lat: -3.10, lon:-60.02, pop: 4200000 },
];

function mapXZ(lat, lon) {
  const latMin=-31, latMax=-1, lonMin=-62, lonMax=-34;
  const x = ((lon - lonMin) / (lonMax - lonMin) - 0.5) * 22;
  const z = ((lat - latMin) / (latMax - latMin) - 0.5) * 18;
  return [x, z];
}

const cityData = {};
REGIONS.forEach(r => {
  const [x, z] = mapXZ(r.lat, r.lon);
  const geo = new THREE.CylinderGeometry(0.38, 0.55, 1.0, 7);
  const mat = new THREE.MeshLambertMaterial({ color: 0xC89B6D });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(x, 0.5, z);
  scene.add(mesh);
  const ringGeo = new THREE.RingGeometry(0.55, 0.75, 7);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x3a2e24, side: THREE.DoubleSide });
  const ring = new THREE.Mesh(ringGeo, ringMat);
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(x, 0.02, z);
  scene.add(ring);
  cityData[r.id] = { mesh, x, z };
});

const PARTICLE_COUNT = 4000;
const pGeo = new THREE.BufferGeometry();
const pPos = new Float32Array(PARTICLE_COUNT * 3);
const pCol = new Float32Array(PARTICLE_COUNT * 3);

const ETHNIC_COLORS = [
  [0.60, 0.40, 0.20],
  [0.75, 0.55, 0.30],
  [0.90, 0.75, 0.60],
  [0.80, 0.60, 0.35],
  [0.85, 0.70, 0.50],
];
const ETHNIC_WEIGHTS = [0.43, 0.28, 0.21, 0.05, 0.03];

function pickColor() {
  let r = Math.random(), cumul = 0;
  for (let i = 0; i < ETHNIC_WEIGHTS.length; i++) {
    cumul += ETHNIC_WEIGHTS[i];
    if (r <= cumul) return ETHNIC_COLORS[i];
  }
  return ETHNIC_COLORS[0];
}

for (let i = 0; i < PARTICLE_COUNT; i++) {
  const ri = Math.floor(Math.random() * REGIONS.length);
  const reg = REGIONS[ri];
  const [rx, rz] = mapXZ(reg.lat, reg.lon);
  pPos[i*3]   = rx + (Math.random() - 0.5) * 3.5;
  pPos[i*3+1] = Math.random() * 3.5 + 0.4;
  pPos[i*3+2] = rz + (Math.random() - 0.5) * 3.0;
  const [cr, cg, cb] = pickColor();
  pCol[i*3] = cr; pCol[i*3+1] = cg; pCol[i*3+2] = cb;
}
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 3));
const pMat = new THREE.PointsMaterial({ size: 0.11, vertexColors: true, transparent: true, opacity: 0.8 });
scene.add(new THREE.Points(pGeo, pMat));

const gridHelper = new THREE.GridHelper(28, 28, 0x2a1f15, 0x241a10);
scene.add(gridHelper);

function el(id) { return document.getElementById(id); }

function updateOverlay(data) {
  if (el('v-year')) el('v-year').textContent = data.year + ' / ' + data.total_years;
  if (el('v-pop')) el('v-pop').textContent = (data.population_size || 0).toLocaleString();
  if (!data.latest_cycle) {
    if (el('v-hdi'))  el('v-hdi').textContent  = '—';
    if (el('v-gini')) el('v-gini').textContent = '—';
    if (el('v-emp'))  el('v-emp').textContent  = '—';
    if (el('v-hint')) el('v-hint').style.display = '';
    return;
  }
  if (el('v-hint')) el('v-hint').style.display = 'none';
  const c = data.latest_cycle;
  if (el('v-hdi'))  el('v-hdi').textContent  = c.aggregate_hdi.toFixed(3);
  if (el('v-gini')) el('v-gini').textContent = c.aggregate_gini.toFixed(3);
  if (el('v-emp'))  el('v-emp').textContent  = (c.aggregate_employment * 100).toFixed(1) + '%';
}

function updateCities(data) {
  if (!data.regions) return;
  data.regions.forEach(r => {
    const entry = cityData[r.region_id];
    if (!entry) return;
    const hdi = r.hdi || 0.7;
    const targetH = 0.5 + hdi * 5.5;
    entry.mesh.scale.y = targetH;
    entry.mesh.position.y = targetH * 0.5;
    const hue = 0.06 + hdi * 0.12;
    const sat = 0.60 + (1 - r.gini) * 0.25;
    const lit = 0.30 + hdi * 0.22;
    entry.mesh.material.color.setHSL(hue, sat, lit);
  });
}

window.updateSimulation = function(data) {
  updateOverlay(data);
  updateCities(data);
};

let angle = 0;
const CAM_R = 30, CAM_H = 16;
function animate() {
  requestAnimationFrame(animate);
  angle += 0.0015;
  camera.position.x = Math.cos(angle) * CAM_R;
  camera.position.z = Math.sin(angle) * CAM_R;
  camera.position.y = CAM_H;
  camera.lookAt(0, 2, 0);
  renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
</script>
</body>
</html>"""


def _create_render_widget(html_content: str) -> tuple[QWidget, bool]:
    try:
        from PySide6.QtWebEngineWidgets import QWebEngineView
        view = QWebEngineView()
        view.setHtml(html_content)
        return view, True
    except Exception:
        lbl = QLabel(_WEBENGINE_UNAVAILABLE_MESSAGE)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl, False


class SimulationTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sim_engine = NationSimulationEngine()
        self._event_matrix = StochasticEventMatrix(seed=42)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(6)

        self.grp_controls = QGroupBox()
        ctl_layout = QVBoxLayout(self.grp_controls)

        self.lbl_status_year = QLabel()
        self.lbl_status_year.setObjectName("SectionHeading")
        ctl_layout.addWidget(self.lbl_status_year)

        self.lbl_status_metrics = QLabel()
        self.lbl_status_metrics.setWordWrap(True)
        ctl_layout.addWidget(self.lbl_status_metrics)

        btn_row = QHBoxLayout()
        self.btn_advance_year = QPushButton()
        self.btn_advance_year.clicked.connect(self._on_advance_year)
        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self._on_reset)
        btn_row.addWidget(self.btn_advance_year)
        btn_row.addWidget(self.btn_reset)
        ctl_layout.addLayout(btn_row)
        outer.addWidget(self.grp_controls)

        self.grp_events = QGroupBox()
        evt_layout = QVBoxLayout(self.grp_events)
        self.lbl_events = QLabel()
        self.lbl_events.setWordWrap(True)
        evt_layout.addWidget(self.lbl_events)
        outer.addWidget(self.grp_events)

        self._render_widget, self._has_webengine = _create_render_widget(_THREE_JS_HTML)
        outer.addWidget(self._render_widget, stretch=1)

        self._refresh_status()
        self._refresh_events()

    def set_group_titles(self, controls_title: str, events_title: str) -> None:
        self.grp_controls.setTitle(controls_title)
        self.grp_events.setTitle(events_title)

    def set_button_texts(self, advance_text: str, reset_text: str) -> None:
        self.btn_advance_year.setText(advance_text)
        self.btn_reset.setText(reset_text)

    def _push_simulation_data(self, json_payload: str) -> None:
        if not self._has_webengine:
            return
        self._render_widget.page().runJavaScript(
            "if(window.updateSimulation){updateSimulation(" + json_payload + ");}"
        )

    def _refresh_status(self) -> None:
        engine = self._sim_engine
        total = engine.SIMULATION_YEARS
        pop = f"{engine.POPULATION_SIZE:,}"
        self.lbl_status_year.setText(f"Year {engine.current_year} / {total}  |  Citizens: {pop}")
        if engine.cycles:
            last = engine.cycles[-1]
            emp_pct = round(last.aggregate_employment * 100, 1)
            self.lbl_status_metrics.setText(
                f"HDI: {last.aggregate_hdi:.3f}  |  GINI: {last.aggregate_gini:.3f}"
                f"  |  Employment: {emp_pct}%"
            )
        else:
            self.lbl_status_metrics.setText("Advance year to begin simulation.")
        self._push_simulation_data(json.dumps(engine.serialise_for_renderer()))

    def _refresh_events(self) -> None:
        if not self._sim_engine.cycles:
            self.lbl_events.setText("No events yet. Advance year to generate the first SEEM cycle.")
            return
        last = self._sim_engine.cycles[-1]
        lines = [
            f"[{e.category}]  {e.title}"
            f"  (severity={e.severity:.2f}, Δgdp={e.gdp_delta:+.2f}, Δwelfare={e.welfare_delta:+.2f})"
            for e in last.events
        ]
        self.lbl_events.setText("\n".join(lines))

    def _on_advance_year(self) -> None:
        engine = self._sim_engine
        if engine.current_year > engine.SIMULATION_YEARS:
            return
        engine.advance_year(self._event_matrix)
        self._refresh_status()
        self._refresh_events()

    def _on_reset(self) -> None:
        self._sim_engine = NationSimulationEngine()
        self._refresh_status()
        self._refresh_events()
