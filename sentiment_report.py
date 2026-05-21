import json
import os
from sentiment_analyzer import SENTIMENT_LEVELS

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

  /* heatmap */
  .heatmap{width:100%;border-collapse:collapse;font-size:.82rem}
  .heatmap th{text-align:left;padding:10px 14px;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155}
  .heatmap td{padding:9px 14px;border-bottom:1px solid #0f172a;cursor:pointer}
  .heatmap tr:hover td{background:#0f172a}
  .heatmap tr.active td{background:#0f172a;border-left:3px solid #6366f1}
  .badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff}
  .stacked{display:flex;height:12px;border-radius:4px;overflow:hidden;gap:1px;min-width:160px}
  .stacked-seg{height:100%;transition:opacity .2s}
  .stacked-seg:hover{opacity:.8}

  /* topic tabs */
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
  .tab{padding:6px 14px;border-radius:8px;font-size:.8rem;cursor:pointer;background:#0f172a;color:#94a3b8;border:1px solid #334155}
  .tab:hover{background:#1e293b;color:#e2e8f0}
  .tab.active{background:#6366f1;color:#fff;border-color:#6366f1}

  /* opinion cards */
  .cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
  .opinion-card{background:#0f172a;border-radius:10px;padding:16px;border:1px solid #1e293b;display:flex;flex-direction:column;gap:10px}
  .card-header{display:flex;align-items:center;justify-content:space-between;gap:8px}
  .card-user{font-size:.8rem;color:#64748b}
  .card-badges{display:flex;gap:6px;flex-wrap:wrap}
  .card-text{font-size:.82rem;color:#cbd5e1;line-height:1.6;max-height:120px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;scrollbar-width:thin;scrollbar-color:#334155 transparent}
  .card-text::-webkit-scrollbar{width:4px}
  .card-text::-webkit-scrollbar-thumb{background:#334155;border-radius:4px}
  .card-footer{display:flex;align-items:center;justify-content:flex-end}
  .reddit-link{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;background:#ff4500;border-radius:6px;color:#fff;font-size:.75rem;font-weight:600;text-decoration:none}
  .reddit-link:hover{background:#e03d00}
  .reddit-icon{font-size:.9rem}
  .no-data{color:#475569;font-size:.85rem;padding:20px 0}

  /* filter bar */
  .controls{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap;align-items:center}
  input[type=text]{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;width:220px;outline:none}
  input[type=text]:focus{border-color:#6366f1}
  select{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;outline:none}
  .count-label{font-size:.8rem;color:#475569;margin-left:auto}
</style>
</head>
<body>
<h1 id="pageTitle"></h1>
<p class="subtitle" id="subtitle"></p>

<div class="section">
  <h2>Topic Overview — click a row to filter opinions below</h2>
  <table class="heatmap" id="heatmap"></table>
</div>

<div class="section">
  <h2>Opinions by Topic</h2>
  <div class="controls">
    <div class="tabs" id="tabs"></div>
  </div>
  <div class="controls">
    <input type="text" id="search" placeholder="Search text or user..." oninput="renderCards()"/>
    <select id="fSentiment" onchange="renderCards()"><option value="">All Sentiments</option></select>
    <span class="count-label" id="cardCount"></span>
  </div>
  <div class="cards-grid" id="cardsGrid"></div>
</div>

<script>
const __DATA__ = __RECORDS_JSON__;
const __META__ = __META_JSON__;
</script>
<script>
const SENTIMENT_COLORS = __SENTIMENT_COLORS_JSON__;
const SENTIMENT_LEVELS = __SENTIMENT_LEVELS_JSON__;

let activeTopic = null;

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

function getTopicMap() {
  const map = {};
  __DATA__.forEach(r => {
    Object.entries(r.topics || {}).forEach(([t, s]) => {
      if (!map[t]) map[t] = {};
      map[t][s] = (map[t][s] || 0) + 1;
    });
  });
  return map;
}

function renderHeatmap() {
  const topicMap = getTopicMap();
  const topics = Object.keys(topicMap).sort();
  if (!topics.length) { document.getElementById('heatmap').innerHTML = '<tr><td class="no-data">No data yet</td></tr>'; return; }

  let html = '<thead><tr><th>Topic</th><th>Dominant</th><th>Distribution</th><th>Mentions</th></tr></thead><tbody>';
  topics.forEach(t => {
    const counts = topicMap[t];
    const total = Object.values(counts).reduce((a,b)=>a+b,0);
    const dom = SENTIMENT_LEVELS.find(s => counts[s] > 0) || 'Neutral';
    html += `<tr onclick="selectTopic('${t}')" id="row-${t.replace(/[^a-z0-9]/gi,'_')}">
      <td><strong>${t}</strong></td>
      <td>${badge(dom)}</td>
      <td>${stackedBar(counts, total)}</td>
      <td>${total}</td>
    </tr>`;
  });
  html += '</tbody>';
  document.getElementById('heatmap').innerHTML = html;
}

function renderTabs() {
  const topics = Object.keys(getTopicMap()).sort();
  const container = document.getElementById('tabs');
  container.innerHTML = '<div class="tab active" onclick="selectTopic(null)" id="tab-all">All Topics</div>' +
    topics.map(t =>
      `<div class="tab" onclick="selectTopic('${t}')" id="tab-${t.replace(/[^a-z0-9]/gi,'_')}">${t}</div>`
    ).join('');

  const fSentiment = document.getElementById('fSentiment');
  fSentiment.innerHTML = '<option value="">All Sentiments</option>';
  SENTIMENT_LEVELS.forEach(s => {
    const o = document.createElement('option'); o.value = o.textContent = s; fSentiment.appendChild(o);
  });
}

function selectTopic(topic) {
  activeTopic = topic;

  // update tab styles
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  const tabId = topic ? 'tab-' + topic.replace(/[^a-z0-9]/gi,'_') : 'tab-all';
  const tabEl = document.getElementById(tabId);
  if (tabEl) tabEl.classList.add('active');

  // update heatmap row highlight
  document.querySelectorAll('.heatmap tr').forEach(el => el.classList.remove('active'));
  if (topic) {
    const rowEl = document.getElementById('row-' + topic.replace(/[^a-z0-9]/gi,'_'));
    if (rowEl) rowEl.classList.add('active');
  }

  renderCards();
}

function renderCards() {
  const q = document.getElementById('search').value.toLowerCase();
  const fs = document.getElementById('fSentiment').value;

  let records = __DATA__;

  if (activeTopic) {
    records = records.filter(r => activeTopic in (r.topics || {}));
  }
  if (fs) {
    records = records.filter(r => Object.values(r.topics || {}).includes(fs));
  }
  if (q) {
    records = records.filter(r =>
      ((r.user_id||'') + ' ' + (r.text_snippet||'')).toLowerCase().includes(q)
    );
  }

  document.getElementById('cardCount').textContent = `${records.length} record${records.length !== 1 ? 's' : ''}`;

  if (!records.length) {
    document.getElementById('cardsGrid').innerHTML = '<p class="no-data">No matching records.</p>';
    return;
  }

  document.getElementById('cardsGrid').innerHTML = records.map(r => {
    const topicsToShow = activeTopic
      ? { [activeTopic]: r.topics[activeTopic] }
      : r.topics || {};

    const badgeHtml = Object.entries(topicsToShow)
      .map(([t, s]) => `<span style="font-size:.7rem;color:#94a3b8">${t}:</span> ${badge(s)}`)
      .join(' ');

    const text = (r.text_snippet || '').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const link = r.post_url
      ? `<a class="reddit-link" href="${r.post_url}" target="_blank"><span class="reddit-icon">&#x1F517;</span> Reddit</a>`
      : '';

    return `<div class="opinion-card">
      <div class="card-header">
        <span class="card-user">u/${r.user_id || 'unknown'}</span>
        ${link}
      </div>
      <div class="card-badges">${badgeHtml}</div>
      <div class="card-text">${text || '<em style="color:#475569">No text</em>'}</div>
    </div>`;
  }).join('');
}

function init() {
  document.getElementById('pageTitle').textContent = __META__.title + ' — Sentiment Report';
  document.getElementById('subtitle').textContent =
    'Last updated: ' + __META__.last_updated + ' UTC  |  ' + __DATA__.length + ' tagged records';
  renderHeatmap();
  renderTabs();
  renderCards();
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
