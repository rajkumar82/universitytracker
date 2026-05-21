import json
import os
from collections import Counter
from datetime import datetime

STATUS_COLORS = {
    "Offered": "#22c55e",
    "Rejected": "#ef4444",
    "Waitlisted": "#f59e0b",
}
PILLAR_COLORS = {
    "CSD/ISTD": "#6366f1", "ISTD": "#6366f1", "ESD": "#0ea5e9",
    "ASD": "#ec4899", "EPD": "#f97316", "DAI": "#14b8a6", "SMT": "#8b5cf6",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__TITLE__ Admission Tracker</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:24px}
  h1{font-size:1.6rem;font-weight:700;margin-bottom:4px}
  .subtitle{color:#94a3b8;font-size:.85rem;margin-bottom:24px}
  .cards{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}
  .card{background:#1e293b;border-radius:12px;padding:20px 24px;flex:1;min-width:140px}
  .card .num{font-size:2rem;font-weight:700}
  .card .lbl{font-size:.8rem;color:#94a3b8;margin-top:4px}
  .card.green .num{color:#22c55e}
  .card.red .num{color:#ef4444}
  .card.amber .num{color:#f59e0b}
  .card.slate .num{color:#94a3b8}
  .panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:28px}
  .panel{background:#1e293b;border-radius:12px;padding:20px}
  .panel h2{font-size:.95rem;font-weight:600;margin-bottom:14px;color:#cbd5e1}
  .panel-sub{font-size:.7rem;font-weight:400;color:#475569;margin-left:6px}
  .bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .bar-label{width:110px;font-size:.8rem;color:#cbd5e1;flex-shrink:0}
  .bar-track{flex:1;background:#334155;border-radius:4px;height:10px;overflow:hidden}
  .bar-fill{height:100%;border-radius:4px}
  .bar-count{width:28px;text-align:right;font-size:.8rem;color:#94a3b8}
  .no-data{color:#64748b;font-size:.8rem}
  .table-wrap{background:#1e293b;border-radius:12px;padding:20px;overflow-x:auto}
  .table-wrap h2{font-size:.95rem;font-weight:600;margin-bottom:14px;color:#cbd5e1}
  .controls{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
  input[type=text]{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;width:240px;outline:none}
  input[type=text]:focus{border-color:#6366f1}
  select{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;outline:none}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:10px 12px;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155;white-space:nowrap}
  td{padding:9px 12px;border-bottom:1px solid #1e293b;vertical-align:top}
  tr:hover td{background:#0f172a}
  .pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff}
  .snippet{max-width:340px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  a{color:#818cf8;text-decoration:none}
  a:hover{text-decoration:underline}
  #count{font-size:.8rem;color:#64748b;margin-bottom:8px}
</style>
</head>
<body>
<h1 id="pageTitle"></h1>
<p class="subtitle" id="subtitle"></p>
<div class="cards" id="cards"></div>
<div class="panels" id="panels"></div>
<div class="table-wrap">
  <h2>All Records</h2>
  <div class="controls">
    <input type="text" id="search" placeholder="Search user, text..." oninput="filterTable()"/>
    <select id="fStatus" onchange="filterTable()"><option value="">All Statuses</option></select>
    <select id="fPillar" onchange="filterTable()"><option value="">All Pillars</option></select>
    <select id="fNat" onchange="filterTable()"><option value="">All Nationalities</option></select>
  </div>
  <div id="count"></div>
  <table><thead><tr>
    <th>User</th><th>Status</th><th>Pillar</th><th>Scholarship</th><th>Nationality</th><th>Snippet</th><th>Source</th>
  </tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
const __DATA__ = __RECORDS_JSON__;
const __META__ = __META_JSON__;
</script>
<script>
const STATUS_COLORS = {"Offered":"#22c55e","Rejected":"#ef4444","Waitlisted":"#f59e0b"};
const PILLAR_COLORS = {"CSD/ISTD":"#6366f1","ISTD":"#6366f1","ESD":"#0ea5e9","ASD":"#ec4899","EPD":"#f97316","DAI":"#14b8a6","SMT":"#8b5cf6"};

function pill(status) {
  const c = STATUS_COLORS[status] || '#94a3b8';
  return `<span class="pill" style="background:${c}">${status || '—'}</span>`;
}

function barRows(records, field, colorMap, label) {
  const total = records.length || 1;
  const counts = {};
  records.forEach(r => { if (r[field]) counts[r[field]] = (counts[r[field]] || 0) + 1; });
  const notDetected = records.length - Object.values(counts).reduce((a, b) => a + b, 0);
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  let html = '';
  sorted.forEach(([k, v]) => {
    const pct = (v / total * 100).toFixed(1);
    const color = (colorMap || {})[k] || '#94a3b8';
    html += `<div class="bar-row">
      <span class="bar-label">${k}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
      <span class="bar-count">${v}</span></div>`;
  });
  if (notDetected > 0) {
    const pct = (notDetected / total * 100).toFixed(1);
    html += `<div class="bar-row">
      <span class="bar-label" style="color:#475569">Not detected</span>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:#334155"></div></div>
      <span class="bar-count" style="color:#475569">${notDetected}</span></div>`;
  }
  return html || '<p class="no-data">No data</p>';
}

function populateFilter(id, records, field) {
  const sel = document.getElementById(id);
  const vals = [...new Set(records.map(r => r[field]).filter(Boolean))].sort();
  vals.forEach(v => { const o = document.createElement('option'); o.value = o.textContent = v; sel.appendChild(o); });
}

function renderRows(records) {
  document.getElementById('tbody').innerHTML = records.map(r => `
    <tr>
      <td>${r.user_id || '—'}</td>
      <td>${pill(r.status)}</td>
      <td>${r.pillar || '—'}</td>
      <td>${r.scholarship || '—'}</td>
      <td>${r.nationality || '—'}</td>
      <td class="snippet">${r.text_snippet || ''}</td>
      <td>${r.post_url ? `<a href="${r.post_url}" target="_blank">view</a>` : '—'}</td>
    </tr>`).join('');
  document.getElementById('count').textContent = `Showing ${records.length} of ${__DATA__.length} records`;
}

function filterTable() {
  const q = document.getElementById('search').value.toLowerCase();
  const st = document.getElementById('fStatus').value;
  const pl = document.getElementById('fPillar').value;
  const nt = document.getElementById('fNat').value;
  renderRows(__DATA__.filter(r =>
    (!q || ((r.user_id||'') + ' ' + (r.text_snippet||'')).toLowerCase().includes(q)) &&
    (!st || r.status === st) && (!pl || r.pillar === pl) && (!nt || r.nationality === nt)
  ));
}

function init() {
  document.getElementById('pageTitle').textContent = __META__.title + ' Admission Tracker';
  document.getElementById('subtitle').textContent = 'Last updated: ' + __META__.last_updated + ' UTC | Source: Reddit';

  const offered = __DATA__.filter(r => r.status === 'Offered');
  const rejected = __DATA__.filter(r => r.status === 'Rejected');
  const waitlisted = __DATA__.filter(r => r.status === 'Waitlisted');
  const unknown = __DATA__.length - offered.length - rejected.length - waitlisted.length;

  document.getElementById('cards').innerHTML = `
    <div class="card"><div class="num">${__DATA__.length}</div><div class="lbl">Total Records</div></div>
    <div class="card green"><div class="num">${offered.length}</div><div class="lbl">Offered</div></div>
    <div class="card red"><div class="num">${rejected.length}</div><div class="lbl">Rejected</div></div>
    <div class="card amber"><div class="num">${waitlisted.length}</div><div class="lbl">Waitlisted</div></div>
    <div class="card slate"><div class="num">${unknown}</div><div class="lbl">Status Unknown</div></div>`;

  document.getElementById('panels').innerHTML = `
    <div class="panel"><h2>By Pillar <span class="panel-sub">offered only</span></h2>${barRows(offered, 'pillar', PILLAR_COLORS)}</div>
    <div class="panel"><h2>By Scholarship <span class="panel-sub">offered only</span></h2>${barRows(offered, 'scholarship', {})}</div>
    <div class="panel"><h2>By Nationality <span class="panel-sub">offered only</span></h2>${barRows(offered, 'nationality', {})}</div>`;

  populateFilter('fStatus', __DATA__, 'status');
  populateFilter('fPillar', __DATA__, 'pillar');
  populateFilter('fNat', __DATA__, 'nationality');
  renderRows(__DATA__);
}

init();
</script>
</body>
</html>"""


def generate(data, output_path="data/report.html", title="Admission Tracker"):
    records = data.get("records", [])
    last_updated = data.get("last_updated", "—")

    records_json = json.dumps(records, ensure_ascii=False)
    meta_json = json.dumps({"title": title, "last_updated": last_updated}, ensure_ascii=False)

    html = (TEMPLATE
            .replace("__TITLE__", title)
            .replace("__RECORDS_JSON__", records_json)
            .replace("__META_JSON__", meta_json))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved: {output_path}")
