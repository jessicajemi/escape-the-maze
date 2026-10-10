"""
Live algorithm visualiser.

One small HTML/JS "player" is used for everything: mazes (grid), trees and graphs,
hill-climbing landscapes, CSP map colouring and means-end-analysis traces.
Python computes the frames (algos.py); the browser plays them back smoothly
(play / pause / step / speed) without re-running Streamlit on every step.
"""
import json
import streamlit as st

from algos import (TREE, WG, LANDSCAPE10, AUS, WHEEL, COLOUR_NAMES)

PLAYER_HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:transparent;color:#e2e8f0}
  #card{background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:12px 12px 10px}
  #title{font-weight:700;font-size:14px;margin:0 2px 8px;color:#f8fafc}
  #stage{display:flex;justify-content:center}
  canvas{max-width:100%;border-radius:10px;background:#0b1220}
  #log{display:none;background:#0b1220;border-radius:10px;padding:10px 12px;height:__LOGH__px;overflow:auto;font-size:13px;line-height:1.5}
  .ln{padding:1px 0;color:#cbd5e1}.ln.cur{color:#fff;font-weight:600}
  .t_diff{color:#fbbf24}.t_sub{color:#f472b6}.t_apply{color:#4ade80}.t_goal{color:#38bdf8;font-weight:700}.t_start{color:#94a3b8}
  #chips{margin-top:8px;display:none}
  .chip{display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:999px;padding:2px 9px;margin:2px 4px 2px 0;font-size:12px;color:#cbd5e1}
  #info{margin-top:8px;background:#111c33;border-radius:10px;padding:8px 11px}
  #note{font-size:14px;min-height:20px;color:#f1f5f9}
  #ds{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:#7dd3fc;margin-top:4px;word-break:break-word}
  #stats{font-size:12px;color:#94a3b8;margin-top:5px}
  #result{font-size:13px;color:#4ade80;font-weight:700;margin-top:5px;display:none}
  #ctl{display:flex;align-items:center;gap:6px;margin-top:9px;flex-wrap:wrap}
  button{background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:5px 11px;font-size:14px;cursor:pointer}
  button:hover{background:#334155} button.on{background:#f59e0b;color:#0f172a;border-color:#f59e0b}
  select{background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:8px;padding:5px 6px;font-size:13px}
  input[type=range]{flex:1;min-width:120px;accent-color:#f59e0b}
  #legend{display:flex;flex-wrap:wrap;gap:4px 12px;margin-top:8px;font-size:12px;color:#94a3b8}
  .sw{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:-1px}
</style></head><body>
<div id="card">
  <div id="title"></div>
  <div id="stage"><canvas id="cv"></canvas></div>
  <div id="log"></div>
  <div id="chips"></div>
  <div id="info"><div id="note"></div><div id="ds"></div><div id="stats"></div><div id="result"></div></div>
  <div id="ctl">
    <button id="bFirst" title="Restart">⏮</button>
    <button id="bPrev" title="Step back">◀</button>
    <button id="bPlay" title="Play / pause">▶ Play</button>
    <button id="bNext" title="Step forward">▶|</button>
    <input id="sl" type="range" min="0" max="0" value="0">
    <select id="sp"><option value="1100">Slow</option><option value="600" selected>Normal</option><option value="250">Fast</option><option value="70">Turbo</option></select>
  </div>
  <div id="legend"></div>
</div>
<script>
const S = __SPEC__;
const F = S.frames || [];
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const $ = id => document.getElementById(id);
let i = 0, timer = null;

$('title').textContent = S.title || '';
if (S.static || F.length <= 1) $('ctl').style.display = 'none';
if (S.static) { $('info').style.display = (F[0] && F[0].note) ? 'block' : 'none'; }
$('legend').innerHTML = (S.legend || []).map(l => `<span><span class="sw" style="background:${l[0]}"></span>${l[1]}</span>`).join('');
if (S.kind === 'trace') { cv.style.display = 'none'; $('stage').style.display = 'none'; $('log').style.display = 'block'; $('chips').style.display = 'block'; }
$('sl').max = Math.max(0, F.length - 1);

// visited-before arrays (honours "reset")
const visBefore = []; { let cur = []; for (let k = 0; k < F.length; k++) { if (F[k].reset) cur = []; visBefore.push(cur.slice()); if (F[k].cur !== null && F[k].cur !== undefined) cur.push(F[k].cur); } }

const C = {wall:'#0b1220', free:'#cbd5e1', vis:'#7dd3fc', fro:'#fbbf24', cur:'#f97316', path:'#22c55e',
           start:'#3b82f6', goal:'#ef4444', node:'#e2e8f0', edge:'#475569', text:'#0f172a'};
const PAL = ['#ef4444','#22c55e','#3b82f6','#eab308'];
const dpr = window.devicePixelRatio || 1;

function setSize(w, h){ cv.width = w*dpr; cv.height = h*dpr; cv.style.width = w+'px'; cv.style.height = h+'px'; ctx.setTransform(dpr,0,0,dpr,0,0); }
function avail(){ return Math.max(260, Math.min(900, ($('card').clientWidth || 600) - 30)); }

function drawGrid(f){
  const W = avail(), cell = Math.max(3, Math.floor(Math.min(W / S.cols, (S.maxh || 420) / S.rows)));
  const w = cell * S.cols, h = cell * S.rows; setSize(w, h);
  const vis = new Uint8Array(S.rows*S.cols), fro = new Uint8Array(S.rows*S.cols), pth = new Uint8Array(S.rows*S.cols);
  (visBefore[i] || []).forEach(n => vis[n] = 1);
  (f.fro || []).forEach(n => fro[n] = 1);
  (f.path || []).forEach(n => pth[n] = 1);
  for (let r = 0; r < S.rows; r++) for (let c = 0; c < S.cols; c++) {
    const n = r*S.cols + c;
    ctx.fillStyle = S.walls[n] ? C.wall : (pth[n] ? C.path : (f.cur === n ? C.cur : (fro[n] ? C.fro : (vis[n] ? C.vis : C.free))));
    ctx.fillRect(c*cell, r*cell, cell, cell);
  }
  const mark = (n, col) => { const r = Math.floor(n/S.cols), c = n % S.cols; ctx.fillStyle = col; ctx.fillRect(c*cell, r*cell, cell, cell);
    ctx.fillStyle = '#fff'; ctx.font = `bold ${Math.max(8,cell-2)}px system-ui`; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(col===C.start?'S':'G', c*cell+cell/2, r*cell+cell/2+1); };
  mark(S.start, C.start); mark(S.goal, C.goal);
}

function drawGraph(f){
  const W = avail(), H = S.h || 330; setSize(W, H);
  const pad = 42, P = n => [pad + S.pos[n][0]*(W-2*pad), pad*0.8 + S.pos[n][1]*(H-2*pad*0.9)];
  const vis = new Set(visBefore[i] || []), fro = new Set(f.fro || []), pth = f.path || [];
  const pe = new Set(); for (let k = 0; k+1 < pth.length; k++) { pe.add(pth[k]+'|'+pth[k+1]); pe.add(pth[k+1]+'|'+pth[k]); }
  ctx.lineCap = 'round';
  (S.edges || []).forEach(e => {
    const [x1,y1] = P(e[0]), [x2,y2] = P(e[1]);
    const onp = pe.has(e[0]+'|'+e[1]);
    ctx.strokeStyle = onp ? C.path : C.edge; ctx.lineWidth = onp ? 5 : 2;
    ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
    if (e.length > 2 && e[2] !== null && e[2] !== undefined) {
      const mx = (x1+x2)/2, my = (y1+y2)/2; ctx.fillStyle = '#0b1220'; ctx.fillRect(mx-11,my-9,22,18);
      ctx.fillStyle = '#fbbf24'; ctx.font = 'bold 12px system-ui'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(e[2], mx, my+1); }
  });
  const R = S.r || 20;
  S.nodes.forEach(n => {
    const [x,y] = P(n.id);
    let fill = C.node;
    if (S.palette && f.col && f.col[n.id] !== undefined) fill = PAL[f.col[n.id]];
    else if (!S.palette) {
      if (pth.includes(n.id)) fill = C.path; else if (f.cur === n.id) fill = C.cur;
      else if (fro.has(n.id)) fill = C.fro; else if (vis.has(n.id)) fill = C.vis;
    }
    ctx.beginPath(); ctx.arc(x,y,R,0,6.2832); ctx.fillStyle = fill; ctx.fill();
    ctx.lineWidth = (f.cur === n.id) ? 4 : 2; ctx.strokeStyle = (f.cur === n.id) ? '#fff' : '#0b1220'; ctx.stroke();
    if (!S.palette && (S.goals ? S.goals.includes(n.id) : n.id === S.goal)) { ctx.beginPath(); ctx.arc(x,y,R+5,0,6.2832); ctx.lineWidth=3; ctx.strokeStyle='#ef4444'; ctx.stroke(); }
    if (n.id === S.start && !S.palette) { ctx.beginPath(); ctx.arc(x,y,R+5,0,6.2832); ctx.lineWidth=3; ctx.strokeStyle='#3b82f6'; ctx.stroke(); }
    ctx.fillStyle = (S.palette && f.col && f.col[n.id] !== undefined) ? '#fff' : C.text;
    ctx.font = `bold ${n.label && n.label.length > 3 ? 10 : 13}px system-ui`; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(n.label || n.id, x, y+1);
    const sub = (f.sub && f.sub[n.id]) || n.sub;
    if (sub) { ctx.fillStyle = '#94a3b8'; ctx.font = '11px system-ui'; ctx.fillText(sub, x, y+R+13); }
  });
}

function drawLand(f){
  const W = avail(), H = S.h || 250; setSize(W, H);
  const v = S.values, n = v.length, padX = 28, padT = 26, padB = 30;
  const mn = Math.min(...v), mx = Math.max(...v);
  const X = k => padX + k*(W-2*padX)/Math.max(1,n-1), Y = val => H-padB - (val-mn)/Math.max(1,(mx-mn))*(H-padT-padB);
  ctx.beginPath(); ctx.moveTo(X(0),H-padB); v.forEach((val,k)=>ctx.lineTo(X(k),Y(val))); ctx.lineTo(X(n-1),H-padB); ctx.closePath();
  ctx.fillStyle = '#17233d'; ctx.fill();
  ctx.beginPath(); v.forEach((val,k)=>k?ctx.lineTo(X(k),Y(val)):ctx.moveTo(X(k),Y(val))); ctx.strokeStyle='#64748b'; ctx.lineWidth=2; ctx.stroke();
  // peaks (runs of equal values count once; switched off for question figures)
  if (S.peaks !== false) {
    let k = 0;
    while (k < n) {
      let j = k; while (j+1 < n && v[j+1] === v[k]) j++;
      const l = k>0 ? v[k-1] : -1e9, r = j<n-1 ? v[j+1] : -1e9;
      if (v[k] > l && v[k] > r) {
        const mid = Math.round((k+j)/2), isG = v[k] === mx;
        ctx.fillStyle = isG ? '#fbbf24' : '#94a3b8'; ctx.font = '11px system-ui'; ctx.textAlign = 'center';
        ctx.fillText(isG ? '★ global max' : (j>k ? 'plateau' : 'local max'), X(mid), Y(v[k])-(n<=12 ? 22 : 9));
      }
      k = j+1;
    }
  }
  const trail = visBefore[i] || [];
  ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 3; ctx.beginPath();
  trail.concat(f.cur!==null&&f.cur!==undefined?[f.cur]:[]).forEach((k,j)=>j?ctx.lineTo(X(k),Y(v[k])):ctx.moveTo(X(k),Y(v[k]))); ctx.stroke();
  v.forEach((val,k)=>{ ctx.beginPath(); ctx.arc(X(k),Y(val),(n>14?3:5),0,6.2832); ctx.fillStyle = trail.includes(k)?'#38bdf8':'#cbd5e1'; ctx.fill(); });
  if (f.cur!==null&&f.cur!==undefined){ ctx.beginPath(); ctx.arc(X(f.cur),Y(v[f.cur]),9,0,6.2832); ctx.fillStyle='#f97316'; ctx.fill(); ctx.lineWidth=3; ctx.strokeStyle='#fff'; ctx.stroke();
    ctx.fillStyle='#0f172a'; ctx.font='bold 9px system-ui'; ctx.textBaseline='middle'; ctx.fillText('AI',X(f.cur),Y(v[f.cur])+1); }
  ctx.fillStyle='#94a3b8'; ctx.font='11px system-ui'; ctx.textAlign='center'; ctx.textBaseline='alphabetic';
  v.forEach((val,k)=>{ if (n<=12 || k%5===0) { ctx.fillText(k, X(k), H-padB+14); } });
  if (n<=12) v.forEach((val,k)=>{ ctx.fillStyle='#e2e8f0'; ctx.fillText(val, X(k), Y(val)+(val===mx?18:-8)); });
  ctx.fillStyle='#64748b'; ctx.fillText('state number →   (height = value, higher is better)', W/2, H-4);
}

function drawTrace(f){
  let h = '';
  for (let k = 0; k <= i; k++) { const g = F[k]; h += `<div class="ln t_${g.type||''} ${k===i?'cur':''}" style="margin-left:${(g.indent||0)*18}px">${k===i?'▶ ':'• '}${g.note}</div>`; }
  $('log').innerHTML = h; $('log').scrollTop = $('log').scrollHeight;
  $('chips').innerHTML = '<span style="font-size:12px;color:#94a3b8">Current state: </span>' + (f.state||[]).map(s => `<span class="chip">${s.replace(/_/g,' ')}</span>`).join('');
}

function draw(){
  const f = F[i] || {};
  if (S.kind === 'grid') drawGrid(f); else if (S.kind === 'graph') drawGraph(f);
  else if (S.kind === 'landscape') drawLand(f); else if (S.kind === 'trace') drawTrace(f);
  $('note').textContent = f.note || ''; $('ds').textContent = f.ds || ''; $('ds').style.display = f.ds ? 'block' : 'none';
  if (S.kind !== 'trace' && !S.static) {
    const vb = (visBefore[i]||[]).length + (f.cur!==null&&f.cur!==undefined?1:0);
    $('stats').textContent = `Step ${i+1} of ${F.length}` + ((S.kind==='landscape' || S.palette) ? '' : ` · visited: ${vb} · frontier: ${(f.fro||[]).length}`);
  } else if (S.kind === 'trace') { $('stats').textContent = `Step ${i+1} of ${F.length}`; } else $('stats').textContent = '';
  const last = (i === F.length-1) && f.result;
  $('result').style.display = last ? 'block' : 'none'; if (last) $('result').textContent = '✔ ' + f.result;
  $('sl').value = i; $('bPlay').textContent = timer ? '⏸ Pause' : '▶ Play'; $('bPlay').className = timer ? 'on' : '';
}
function stop(){ if (timer){ clearInterval(timer); timer = null; } }
function play(){ if (timer){ stop(); draw(); return; } if (i >= F.length-1) i = 0;
  timer = setInterval(() => { if (i < F.length-1) { i++; draw(); } else { stop(); draw(); } }, +$('sp').value); draw(); }
$('bPlay').onclick = play;
$('bNext').onclick = () => { stop(); if (i < F.length-1) i++; draw(); };
$('bPrev').onclick = () => { stop(); if (i > 0) i--; draw(); };
$('bFirst').onclick = () => { stop(); i = 0; draw(); };
$('sl').oninput = e => { stop(); i = +e.target.value; draw(); };
$('sp').onchange = () => { if (timer){ stop(); play(); } };
window.addEventListener('resize', draw);
if (S.startAtEnd) i = F.length - 1;
draw();
if (S.autoplay) play();
</script></body></html>"""


def render_player(spec, height=520):
    """Embed the player. `spec` is a plain dict (see build_* helpers below)."""
    logh = 230
    html = (PLAYER_HTML.replace("__SPEC__", json.dumps(spec))
            .replace("__LOGH__", str(logh)))
    st.iframe(html, height=height)


# ─────────────────────────── spec builders ───────────────────────────

LEG_SEARCH = [("#f97316", "current"), ("#7dd3fc", "visited"), ("#fbbf24", "frontier / waiting"),
              ("#22c55e", "final path"), ("#3b82f6", "start"), ("#ef4444", "goal")]


def tree_spec(frames=None, title="", static=False):
    nodes = [dict(id=k, label=k) for k in TREE["pos"]]
    edges = [[a, b] for a, kids in TREE["children"].items() for b in kids]
    return dict(kind="graph", title=title, nodes=nodes, edges=edges, pos=TREE["pos"],
                start="S", goal="G", h=300, frames=frames or [dict(cur=None, note="")],
                legend=[] if static else LEG_SEARCH, static=static)


def wgraph_spec(frames=None, title="", static=False):
    nodes = [dict(id=k, label=k, sub=f"h={WG['h'][k]}") for k in WG["pos"]]
    edges = [[a, b, w] for a, b, w in WG["edges"]]
    return dict(kind="graph", title=title, nodes=nodes, edges=edges, pos=WG["pos"],
                start="S", goal="G", h=280, frames=frames or [dict(cur=None, note="")],
                legend=[] if static else LEG_SEARCH, static=static)


def landscape_spec(values, frames=None, title="", static=False, h=250, peaks=True):
    return dict(kind="landscape", title=title, values=values, h=h, peaks=peaks,
                frames=frames or [dict(cur=None, note="")], static=static,
                legend=[] if static else [("#f97316", "agent (AI)"), ("#38bdf8", "path taken"),
                                          ("#fbbf24", "global maximum")])


def csp_spec(g, frames=None, title="", static=False, assigned=None, ncol=3):
    nodes = [dict(id=k, label=k) for k in g["pos"]]
    edges = [list(e) for e in g["edges"]]
    fr = frames or [dict(cur=None, col=assigned or {}, note="")]
    return dict(kind="graph", title=title, nodes=nodes, edges=edges, pos=g["pos"],
                start=None, goal=None, h=300, r=24, palette=True, frames=fr, static=static,
                legend=[(c, n) for c, n in zip(["#ef4444", "#22c55e", "#3b82f6", "#eab308"],
                                               COLOUR_NAMES[:ncol])])


def grid_spec(g, frames, start, goal, title=""):
    R, C = len(g), len(g[0])
    walls = [1 if g[r][c] else 0 for r in range(R) for c in range(C)]
    return dict(kind="grid", title=title, rows=R, cols=C, walls=walls, start=start,
                goal=goal, frames=frames, legend=LEG_SEARCH, maxh=400)


def trace_spec(frames, title=""):
    return dict(kind="trace", title=title, frames=frames, legend=[])


def jug_spec(frames, pos, tree_edges, goals, title=""):
    sid = lambda s: f"{s[0]},{s[1]}"
    nodes = [dict(id=sid(s), label=f"{s[0]},{s[1]}") for s in pos]
    edges = [[sid(a), sid(b)] for a, b in tree_edges]
    fr = []
    for f in frames:
        g = dict(f)
        g["cur"] = sid(f["cur"]) if f.get("cur") else None
        g["fro"] = [sid(s) for s in f.get("fro", [])]
        if f.get("path"):
            g["path"] = [sid(s) for s in f["path"]]
        fr.append(g)
    gs = goals[0]
    return dict(kind="graph", title=title, nodes=nodes, edges=edges,
                pos={sid(s): p for s, p in pos.items()}, start="0,0", goal=sid(gs),
                goals=[sid(x) for x in goals],
                h=360, r=17, frames=fr, legend=LEG_SEARCH + [])
