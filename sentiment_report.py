import json
import os
from sentiment_analyzer import SENTIMENT_LEVELS, aggregate

SENTIMENT_COLORS = {
    "Excellent": "#22c55e",
    "Good":      "#86efac",
    "Neutral":   "#94a3b8",
    "Bad":       "#f97316",
    "Worst":     "#ef4444",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>__TITLE__ Sentiment Report</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:24px}
  h1{font-size:1.6rem;font-weight:700;margin-bottom:4px}
  h2{font-size:1rem;font-weight:600;color:#cbd5e1;margin-bottom:14px}
  .subtitle{color:#94a3b8;font-size:.85rem;margin-bottom:24px}
  .section{background:#1e293b;border-radius:12px;padding:20px;margin-bottom:20px}
  .heatmap{width:100%;border-collapse:collapse;font-size:.82rem;margin-bottom:8px}
  .heatmap th{text-align:left;padding:10px 14px;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155}
  .heatmap td{padding:9px 14px;border-bottom:1px solid #0f172a}
  .heatmap tr:hover td{background:#0f172a}
  .badge{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff}
  .stacked{display:flex;height:12px;border-radius:4px;overflow:hidden;gap:1px;min-width:160px}
  .stacked-seg{height:100%}
  .panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:20px}
  .panel{background:#1e293b;border-radius:12px;padding:20px}
  .bar-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
  .bar-label{width:80px;font-size:.8rem;color:#cbd5e1;flex-shrink:0}
  .bar-track{flex:1;background:#334155;border-radius:4px;height:10px;overflow:hidden}
  .bar-fill{height:100%;border-radius:4px}
  .bar-count{width:28px;text-align:right;font-size:.8rem;color:#94a3b8}
  .table-wrap{background:#1e293b;border-radius:12px;padding:20px;overflow-x:auto}
  .controls{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}
  input[type=text]{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;width:220px;outline:none}
  input[type=text]:focus{border-color:#6366f1}
  select{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;outline:none}
  table{width:100%;border-collapse:collapse;font-size:.82rem}
  th{text-align:left;padding:10px 12px;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155;white-space:nowrap}
  td{padding:9px 12px;border-bottom:1px solid #1e293b;vertical-align:top}
  tr:hover td{background:#0f172a}
  .snippet{max-width:300px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  a{color:#818cf8;text-decoration:none}
  a:hover{text-decoration:underline}
  #count{font-size:.8rem;color:#64748b;margin-bottom:8px}
  .no-data{color:#475569;font-size:.8rem}
</style>
</head>
<body>
<h1 id="pageTitle"></h1>
<p class="subtitle" id="subtitle"></p>

<div class="section">
  <h2>Topic Overview</h2>
  <table class="heatmap" id="heatmap"></table>
</div>

<div class="panels" id="panels"></div>

<div class="table-wrap">
  <h2>All Tagged Posts &amp; Comments</h2>
  <div class="controls">
    <input type="text" id="search" placeholder="Search user, text..." oninput="filterTable()"/>
    <select id="fTopic" onchange="filterTable()"><option value="">All Topics</option></select>
    <select id="fSentiment" onchange="filterTable()"><option value="">All Sentiments</option></select>
  </div>
  <div id="count"></div>
  <table><thead><tr>
    <th>User</th><th>Topics</th><th>Snippet</th><th>Source</th>
  </tr></thead><tbody id="tbody"></tbody></table>
</div>

<script>
const __DATA__ = __RECORDS_JSON__;
const __META__ = __META_JSON__;
</script>
<script>
const SENTIMENT_COLORS = __SENTIMENT_COLORS_JSON__;
const SENTIMENT_LEVELS = __SENTIMENT_LEVELS_JSON__;

function badge(sentiment) {
  const c = SENTIMENT_COLORS[sentiment] || '#94a3b8';
  return `<span class="badge" style="background:${c}">${sentiment}</span>`;
}

function stackedBar(counts, total) {
  if (!total) return '<span class="no-data">—</span>';
  return '<div class="stacked">' + SENTIMENT_LEVELS.map(s => {
    const n = counts[s] || 0;
    if (!n) return '';
    const pct = (n / total * 100).toFixed(1);
    return `<div class="stacked-seg" style="width:${pct}%;background:${SENTIMENT_COLORS[s]}" title="${s}: ${n}"></div>`;
  }).join('') + '</div>';
}

function dominantSentiment(counts) {
  return SENTIMENT_LEVELS.find(s => counts[s] > 0) || 'Neutral';
}

function renderHeatmap() {
  const topicMap = {};
  __DATA__.forEach(r => {
    Object.entries(r.topics || {}).forEach(([t, s]) => {
      if (!topicMap[t]) topicMap[t] = {};
      topicMap[t][s] = (topicMap[t][s] || 0) + 1;
    });
  });

  const topics = Object.keys(topicMap).sort();
  if (!topics.length) { document.getElementById('heatmap').innerHTML = '<tr><td class="no-data">No data</td></tr>'; return; }

  let html = '<thead><tr><th>Topic</th><th>Overall</th><th>Distribution</th><th>Count</th></tr></thead><tbody>';
  topics.forEach(t => {
    const counts = topicMap[t];
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    const dom = dominantSentiment(counts);
    html += `<tr>
      <td>${t}</td>
      <td>${badge(dom)}</td>
      <td>${stackedBar(counts, total)}</td>
      <td>${total}</td>
    </tr>`;
  });
  html += '</tbody>';
  document.getElementById('heatmap').innerHTML = html;
}

function renderPanels() {
  const topicMap = {};
  __DATA__.forEach(r => {
    Object.entries(r.topics || {}).forEach(([t, s]) => {
      if (!topicMap[t]) topicMap[t] = {};
      topicMap[t][s] = (topicMap[t][s] || 0) + 1;
    });
  });

  const topics = Object.keys(topicMap).sort();
  document.getElementById('panels').innerHTML = topics.map(t => {
    const counts = topicMap[t];
    const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
    const bars = SENTIMENT_LEVELS.map(s => {
      const n = counts[s] || 0;
      if (!n) return '';
      const pct = (n / total * 100).toFixed(1);
      return `<div class="bar-row">
        <span class="bar-label">${s}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${SENTIMENT_COLORS[s]}"></div></div>
        <span class="bar-count">${n}</span></div>`;
    }).join('');
    return `<div class="panel"><h2>${t}</h2>${bars || '<p class="no-data">No data</p>'}</div>`;
  }).join('');
}

function renderRows(records) {
  document.getElementById('tbody').innerHTML = records.map(r => {
    const topicBadges = Object.entries(r.topics || {})
      .map(([t, s]) => `${t}: ${badge(s)}`).join(' ');
    return `<tr>
      <td>${r.user_id || '—'}</td>
      <td style="white-space:nowrap">${topicBadges || '—'}</td>
      <td class="snippet">${r.text_snippet || ''}</td>
      <td>${r.post_url ? `<a href="${r.post_url}" target="_blank">view</a>` : '—'}</td>
    </tr>`;
  }).join('');
  document.getElementById('count').textContent = `Showing ${records.length} of ${__DATA__.length} records`;
}

function populateFilters() {
  const topics = [...new Set(__DATA__.flatMap(r => Object.keys(r.topics || {})))].sort();
  const fTopic = document.getElementById('fTopic');
  topics.forEach(t => { const o = document.createElement('option'); o.value = o.textContent = t; fTopic.appendChild(o); });

  const fSentiment = document.getElementById('fSentiment');
  SENTIMENT_LEVELS.forEach(s => { const o = document.createElement('option'); o.value = o.textContent = s; fSentiment.appendChild(o); });
}

function filterTable() {
  const q = document.getElementById('search').value.toLowerCase();
  const ft = document.getElementById('fTopic').value;
  const fs = document.getElementById('fSentiment').value;
  renderRows(__DATA__.filter(r => {
    const text = ((r.user_id||'') + ' ' + (r.text_snippet||'')).toLowerCase();
    const topics = r.topics || {};
    const matchTopic = !ft || ft in topics;
    const matchSentiment = !fs || Object.values(topics).includes(fs);
    const matchSearch = !q || text.includes(q);
    return matchTopic && matchSentiment && matchSearch;
  }));
}

function init() {
  document.getElementById('pageTitle').textContent = __META__.title + ' Sentiment Report';
  document.getElementById('subtitle').textContent =
    'Last updated: ' + __META__.last_updated + ' UTC | ' + __DATA__.length + ' tagged records';
  renderHeatmap();
  renderPanels();
  populateFilters();
  renderRows(__DATA__);
}

init();
</script>
</body>
</html>"""


def generate(sentiment_data, output_path, title="Sentiment Report"):
    records = sentiment_data.get("records", [])
    last_updated = sentiment_data.get("last_updated", "—")

    records_json = json.dumps(records, ensure_ascii=False)
    meta_json = json.dumps({"title": title, "last_updated": last_updated}, ensure_ascii=False)
    sentiment_colors_json = json.dumps(SENTIMENT_COLORS, ensure_ascii=False)
    sentiment_levels_json = json.dumps(SENTIMENT_LEVELS, ensure_ascii=False)

    html = (TEMPLATE
            .replace("__TITLE__", title)
            .replace("__RECORDS_JSON__", records_json)
            .replace("__META_JSON__", meta_json)
            .replace("__SENTIMENT_COLORS_JSON__", sentiment_colors_json)
            .replace("__SENTIMENT_LEVELS_JSON__", sentiment_levels_json))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Sentiment report saved: {output_path}")
