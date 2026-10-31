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
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #16110E; color: #F4EAD8; font-family: monospace; overflow: hidden; width: 100vw; height: 100vh; }
canvas { display: block; position: absolute; top: 0; left: 0; }
#hud {
  position: absolute; top: 12px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.90); border: 1px solid #3a2e24;
  padding: 10px 14px; border-radius: 4px; min-width: 210px;
}
#hud .section { font-size: 10px; color: #7a6a5a; letter-spacing: 1px; margin-bottom: 5px; margin-top: 8px; }
#hud .section:first-child { margin-top: 0; }
#hud .row { font-size: 12px; color: #C89B6D; margin-bottom: 3px; display: flex; justify-content: space-between; gap: 12px; }
#hud .val { color: #F4EAD8; font-weight: bold; }
#hud .hint { font-size: 11px; color: #7a6a5a; margin-top: 6px; font-style: italic; }
#legend {
  position: absolute; bottom: 12px; left: 12px; z-index: 10;
  background: rgba(22,17,14,0.90); border: 1px solid #3a2e24;
  padding: 8px 12px; border-radius: 4px;
}
#legend .leg-hdr { font-size: 10px; color: #C89B6D; letter-spacing: 1px; margin-bottom: 7px; }
#legend .leg-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 11px; color: #9a8a7a; }
#legend .sw { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
#events {
  position: absolute; bottom: 12px; right: 12px; z-index: 10;
  background: rgba(22,17,14,0.90); border: 1px solid #3a2e24;
  padding: 8px 12px; border-radius: 4px; max-width: 360px;
  max-height: 140px; overflow: hidden;
}
#events .ev-hdr { font-size: 10px; color: #C89B6D; letter-spacing: 1px; margin-bottom: 6px; }
#events .ev-line { font-size: 11px; color: #84A97C; margin-bottom: 3px; line-height: 1.4; }
#title {
  position: absolute; top: 12px; left: 50%; transform: translateX(-50%);
  z-index: 10; color: #C89B6D; font-size: 12px; letter-spacing: 3px;
  text-transform: uppercase; pointer-events: none; white-space: nowrap;
}
</style>
</head>
<body>
<div id="title">CIBERSOC &mdash; SEEM Engine &middot; Simulação Nacional</div>
<div id="hud">
  <div class="section">CICLO DEMÁRQUICO</div>
  <div class="row">Ano<span class="val" id="v-year">1 / 10</span></div>
  <div class="row">Cidadãos<span class="val" id="v-pop">1.000.000</span></div>
  <div class="section">MÉTRICAS AGREGADAS</div>
  <div class="row">IDH médio<span class="val" id="v-hdi">—</span></div>
  <div class="row">GINI médio<span class="val" id="v-gini">—</span></div>
  <div class="row">Emprego<span class="val" id="v-emp">—</span></div>
  <div class="hint" id="v-hint">▶ Avance o ano para iniciar a simulação</div>
</div>
<div id="legend">
  <div class="leg-hdr">LEGENDA VISUAL</div>
  <div class="leg-row"><div class="sw" style="background:#84A97C"></div>Torre alta = IDH elevado</div>
  <div class="leg-row"><div class="sw" style="background:#C26653"></div>Torre curta = IDH baixo</div>
  <div class="leg-row"><div class="sw" style="background:#C89B6D;border-radius:50%"></div>Anel basal = tamanho da população</div>
  <div class="leg-row"><div class="sw" style="background:#d4b896;border-radius:50%"></div>Partículas = cidadãos sorteáveis (diversidade étnica)</div>
</div>
<div id="events">
  <div class="ev-hdr">EVENTOS SEEM</div>
  <div id="ev-body"><div class="ev-line" style="color:#7a6a5a">Nenhum evento ainda.</div></div>
</div>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.min.js"}}
</script>
<script type="module">
import * as THREE from 'three';

const W = () => window.innerWidth, H = () => window.innerHeight;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x16110E);

const camera = new THREE.PerspectiveCamera(52, W() / H(), 0.1, 300);
camera.position.set(4, 26, 38);
camera.lookAt(4, 0, 1);

const renderer = new THREE.WebGLRenderer({ antialias: true });
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

const REGIONS = [
  {id:"BR-SP",name:"São Paulo",         lat:-23.55,lon:-46.63,pop:45000000},
  {id:"BR-RJ",name:"Rio de Janeiro",    lat:-22.91,lon:-43.17,pop:17000000},
  {id:"BR-MG",name:"Minas Gerais",      lat:-19.92,lon:-43.94,pop:21000000},
  {id:"BR-BA",name:"Bahia",             lat:-12.97,lon:-38.50,pop:14000000},
  {id:"BR-PR",name:"Paraná",            lat:-25.42,lon:-49.27,pop:11000000},
  {id:"BR-RS",name:"Rio G. do Sul",     lat:-30.03,lon:-51.22,pop:11000000},
  {id:"BR-PE",name:"Pernambuco",        lat: -8.05,lon:-34.90,pop: 9600000},
  {id:"BR-CE",name:"Ceará",             lat: -3.72,lon:-38.54,pop: 9200000},
  {id:"BR-PA",name:"Pará",              lat: -1.46,lon:-48.50,pop: 8700000},
  {id:"BR-AM",name:"Amazonas",          lat: -3.10,lon:-60.02,pop: 4200000},
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
  const hi = new THREE.Color(0x84A97C);
  const c = new THREE.Color();
  if (hdi < 0.5) c.lerpColors(lo, mid, hdi * 2);
  else c.lerpColors(mid, hi, (hdi - 0.5) * 2);
  return c;
}

function makeLabel(text, sub) {
  const canvas = document.createElement('canvas');
  canvas.width = 320; canvas.height = 80;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, 320, 80);
  ctx.fillStyle = 'rgba(22,17,14,0.78)';
  ctx.fillRect(0, 0, 320, 80);
  ctx.font = 'bold 22px monospace';
  ctx.fillStyle = '#F4EAD8';
  ctx.textAlign = 'center';
  ctx.fillText(text, 160, 30);
  ctx.font = '16px monospace';
  ctx.fillStyle = '#C89B6D';
  ctx.fillText(sub, 160, 58);
  const tex = new THREE.CanvasTexture(canvas);
  const mat = new THREE.SpriteMaterial({map: tex, transparent: true, depthTest: false});
  const sprite = new THREE.Sprite(mat);
  sprite.scale.set(5.5, 1.4, 1);
  return sprite;
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
const pPositions = [];
const pColors = [];
const pPhase = [];
const pCityX = [];
const pCityZ = [];
const pRadius = [];

REGIONS.forEach(r => {
  const [cx, cz] = mapXZ(r.lat, r.lon);
  const hdi = 0.75;
  const towerH = 0.5 + hdi * 5.0;

  const tGeo = new THREE.CylinderGeometry(0.30, 0.50, towerH, 8);
  const tMat = new THREE.MeshLambertMaterial({color: hdiColor(hdi)});
  const tower = new THREE.Mesh(tGeo, tMat);
  tower.position.set(cx, towerH / 2, cz);
  scene.add(tower);

  const popR = 0.7 + (r.pop / POP_MAX) * 2.2;
  const rGeo = new THREE.RingGeometry(popR, popR + 0.18, 32);
  const rMat = new THREE.MeshBasicMaterial({color: 0xC89B6D, side: THREE.DoubleSide, transparent: true, opacity: 0.55});
  const ring = new THREE.Mesh(rGeo, rMat);
  ring.rotation.x = -Math.PI / 2;
  ring.position.set(cx, 0.02, cz);
  scene.add(ring);

  const label = makeLabel(r.name, 'IDH — | Pop ' + (r.pop / 1e6).toFixed(1) + 'M');
  label.position.set(cx, towerH + 2.2, cz);
  scene.add(label);

  cityData[r.id] = {tower, tMat, label, ring, rMat, cx, cz, towerH, popR};

  for (let i = 0; i < PARTS_PER_REGION; i++) {
    const angle = Math.random() * Math.PI * 2;
    const rad = popR + 0.3 + Math.random() * 1.6;
    pPositions.push(cx, Math.random() * 2.5 + 0.3, cz);
    const [cr,cg,cb] = pickEthnic();
    pColors.push(cr, cg, cb);
    pPhase.push(angle);
    pCityX.push(cx);
    pCityZ.push(cz);
    pRadius.push(rad);
  }
});

const pCount = pPositions.length / 3;
const pGeo = new THREE.BufferGeometry();
const pPos = new Float32Array(pPositions);
const pCol = new Float32Array(pColors);
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color',    new THREE.BufferAttribute(pCol, 3));
const pMat = new THREE.PointsMaterial({size: 0.13, vertexColors: true, transparent: true, opacity: 0.82});
const points = new THREE.Points(pGeo, pMat);
scene.add(points);

const groundGeo = new THREE.PlaneGeometry(40, 36);
const groundMat = new THREE.MeshBasicMaterial({color: 0x1c1410, side: THREE.DoubleSide});
const ground = new THREE.Mesh(groundGeo, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.set(4, -0.01, 1);
scene.add(ground);

const grid = new THREE.GridHelper(42, 42, 0x2a1e14, 0x221810);
grid.position.set(4, 0, 1);
scene.add(grid);

function el(id) { return document.getElementById(id); }

let _evCache = [];

window.updateSimulation = function(data) {
  if (el('v-year')) el('v-year').textContent = data.year + ' / ' + data.total_years;
  if (el('v-pop'))  el('v-pop').textContent  = (data.population_size||0).toLocaleString('pt-BR');
  const hasC = !!data.latest_cycle;
  if (el('v-hint')) el('v-hint').style.display = hasC ? 'none' : '';
  if (hasC) {
    const c = data.latest_cycle;
    if (el('v-hdi'))  el('v-hdi').textContent  = c.aggregate_hdi.toFixed(3);
    if (el('v-gini')) el('v-gini').textContent  = c.aggregate_gini.toFixed(3);
    if (el('v-emp'))  el('v-emp').textContent   = (c.aggregate_employment*100).toFixed(1)+'%';
    if (c.events && c.events.length) {
      _evCache = c.events;
      const body = el('ev-body');
      if (body) {
        body.innerHTML = _evCache.map(e =>
          '<div class="ev-line">[' + e.category + '] ' + e.title + '</div>'
        ).join('');
      }
    }
  } else {
    if (el('v-hdi'))  el('v-hdi').textContent  = '—';
    if (el('v-gini')) el('v-gini').textContent  = '—';
    if (el('v-emp'))  el('v-emp').textContent   = '—';
  }
  if (data.regions) {
    data.regions.forEach(r => {
      const d = cityData[r.region_id];
      if (!d) return;
      const hdi = r.hdi || 0.7;
      const newH = 0.5 + hdi * 5.0;
      d.tower.scale.y = newH / d.towerH;
      d.tower.position.y = newH / 2;
      d.tMat.color.copy(hdiColor(hdi));
      d.label.position.y = newH + 2.2;
      const c = d.label.material.map.image;
      const ctx = c.getContext('2d');
      ctx.clearRect(0,0,320,80);
      ctx.fillStyle='rgba(22,17,14,0.78)';ctx.fillRect(0,0,320,80);
      ctx.font='bold 22px monospace';ctx.fillStyle='#F4EAD8';ctx.textAlign='center';
      ctx.fillText(REGIONS.find(x=>x.id===r.region_id).name,160,30);
      ctx.font='16px monospace';ctx.fillStyle='#C89B6D';
      ctx.fillText('IDH '+hdi.toFixed(3)+' | GINI '+r.gini.toFixed(3),160,58);
      d.label.material.map.needsUpdate=true;
    });
  }
};

let t = 0;
const CAM_CX = 4, CAM_CZ = 1, CAM_R = 38, CAM_H = 26;
function animate() {
  requestAnimationFrame(animate);
  t += 0.0008;
  camera.position.x = CAM_CX + Math.cos(t) * CAM_R;
  camera.position.z = CAM_CZ + Math.sin(t) * CAM_R;
  camera.position.y = CAM_H;
  camera.lookAt(CAM_CX, 1, CAM_CZ);

  const pos = pGeo.attributes.position.array;
  for (let i = 0; i < pCount; i++) {
    pPhase[i] += 0.004 + (i % 5) * 0.0006;
    pos[i*3]   = pCityX[i] + Math.cos(pPhase[i]) * pRadius[i];
    pos[i*3+2] = pCityZ[i] + Math.sin(pPhase[i]) * pRadius[i];
  }
  pGeo.attributes.position.needsUpdate = true;

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
