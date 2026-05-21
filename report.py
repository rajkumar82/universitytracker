from collections import Counter
from datetime import datetime
import json
import os

STATUS_COLORS = {
    "Offered": "#22c55e",
    "Rejected": "#ef4444",
    "Waitlisted": "#f59e0b",
}
PILLAR_COLORS = {
    "ISTD": "#6366f1",
    "ESD": "#0ea5e9",
    "ASD": "#ec4899",
    "EPD": "#f97316",
    "DAI": "#14b8a6",
    "SMT": "#8b5cf6",
}


def _bar_rows(records, field, color_map=None):
    detected = [r for r in records if r.get(field)]
    not_detected = len(records) - len(detected)
    counts = Counter(r[field] for r in detected)
    total = len(records) or 1
    rows = []
    for label, count in counts.most_common():
        pct = count / total * 100
        color = (color_map or {}).get(label, "#94a3b8")
        rows.append(f"""
        <div class="bar-row">
          <span class="bar-label">{label}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>
          </div>
          <span class="bar-count">{count}</span>
        </div>""")
    if not_detected:
        pct = not_detected / total * 100
        rows.append(f"""
        <div class="bar-row">
          <span class="bar-label" style="color:#475569">Not detected</span>
          <div class="bar-track">
            <div class="bar-fill" style="width:{pct:.1f}%;background:#334155"></div>
          </div>
          <span class="bar-count" style="color:#475569">{not_detected}</span>
        </div>""")
    return "".join(rows) if rows else "<p class='no-data'>No data</p>"


def _table_rows(records):
    rows = []
    for r in records:
        status = r.get("status") or ""
        color = STATUS_COLORS.get(status, "#94a3b8")
        pill = f'<span class="pill" style="background:{color}">{status or "—"}</span>'
        url = r.get("post_url", "")
        link = f'<a href="{url}" target="_blank">view</a>' if url else "—"
        rows.append(f"""
        <tr>
          <td>{r.get("user_id","—")}</td>
          <td>{pill}</td>
          <td>{r.get("pillar") or "—"}</td>
          <td>{r.get("scholarship") or "—"}</td>
          <td>{r.get("nationality") or "—"}</td>
          <td class="snippet">{r.get("text_snippet","")}</td>
          <td>{link}</td>
        </tr>""")
    return "".join(rows)


def generate(data, output_path="data/report.html", title="Admission Tracker"):
    records = data.get("records", [])
    total = len(records)
    last_updated = data.get("last_updated", "—")
    offered = sum(1 for r in records if r.get("status") == "Offered")
    rejected = sum(1 for r in records if r.get("status") == "Rejected")
    waitlisted = sum(1 for r in records if r.get("status") == "Waitlisted")
    unknown = total - offered - rejected - waitlisted

    records_json = json.dumps(records, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title} Admission Tracker</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:24px}}
  h1{{font-size:1.6rem;font-weight:700;margin-bottom:4px}}
  .subtitle{{color:#94a3b8;font-size:.85rem;margin-bottom:24px}}
  .cards{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}}
  .card{{background:#1e293b;border-radius:12px;padding:20px 24px;flex:1;min-width:140px}}
  .card .num{{font-size:2rem;font-weight:700}}
  .card .lbl{{font-size:.8rem;color:#94a3b8;margin-top:4px}}
  .card.green .num{{color:#22c55e}}
  .card.red .num{{color:#ef4444}}
  .card.amber .num{{color:#f59e0b}}
  .card.slate .num{{color:#94a3b8}}
  .panels{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-bottom:28px}}
  .panel{{background:#1e293b;border-radius:12px;padding:20px}}
  .panel h2{{font-size:.95rem;font-weight:600;margin-bottom:14px;color:#cbd5e1}}
  .bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
  .bar-label{{width:90px;font-size:.8rem;color:#cbd5e1;flex-shrink:0}}
  .bar-track{{flex:1;background:#334155;border-radius:4px;height:10px;overflow:hidden}}
  .bar-fill{{height:100%;border-radius:4px;transition:width .3s}}
  .bar-count{{width:28px;text-align:right;font-size:.8rem;color:#94a3b8}}
  .no-data{{color:#64748b;font-size:.8rem}}
  .table-wrap{{background:#1e293b;border-radius:12px;padding:20px;overflow-x:auto}}
  .table-wrap h2{{font-size:.95rem;font-weight:600;margin-bottom:14px;color:#cbd5e1}}
  .controls{{display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap}}
  input[type=text]{{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;width:240px;outline:none}}
  input[type=text]:focus{{border-color:#6366f1}}
  select{{background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px 12px;font-size:.85rem;outline:none}}
  table{{width:100%;border-collapse:collapse;font-size:.82rem}}
  th{{text-align:left;padding:10px 12px;color:#94a3b8;font-weight:600;border-bottom:1px solid #334155;white-space:nowrap}}
  td{{padding:9px 12px;border-bottom:1px solid #1e293b;vertical-align:top}}
  tr:hover td{{background:#0f172a}}
  .pill{{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.75rem;font-weight:600;color:#fff}}
  .snippet{{max-width:340px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  a{{color:#818cf8;text-decoration:none}}
  a:hover{{text-decoration:underline}}
  #count{{font-size:.8rem;color:#64748b;margin-bottom:8px}}
</style>
</head>
<body>
<h1>{title} Admission Tracker</h1>
<p class="subtitle">Last updated: {last_updated} UTC &nbsp;|&nbsp; Source: Reddit</p>

<div class="cards">
  <div class="card"><div class="num">{total}</div><div class="lbl">Total Records</div></div>
  <div class="card green"><div class="num">{offered}</div><div class="lbl">Offered</div></div>
  <div class="card red"><div class="num">{rejected}</div><div class="lbl">Rejected</div></div>
  <div class="card amber"><div class="num">{waitlisted}</div><div class="lbl">Waitlisted</div></div>
  <div class="card slate"><div class="num">{unknown}</div><div class="lbl">Status Unknown</div></div>
</div>

<div class="panels">
  <div class="panel">
    <h2>By Pillar</h2>
    {_bar_rows(records, "pillar", PILLAR_COLORS)}
  </div>
  <div class="panel">
    <h2>By Scholarship</h2>
    {_bar_rows(records, "scholarship")}
  </div>
  <div class="panel">
    <h2>By Nationality</h2>
    {_bar_rows(records, "nationality")}
  </div>
</div>

<div class="table-wrap">
  <h2>All Records</h2>
  <div class="controls">
    <input type="text" id="search" placeholder="Search user, text…" oninput="filterTable()"/>
    <select id="fStatus" onchange="filterTable()">
      <option value="">All Statuses</option>
      <option>Offered</option><option>Rejected</option><option>Waitlisted</option>
    </select>
    <select id="fPillar" onchange="filterTable()">
      <option value="">All Pillars</option>
      <option>ISTD</option><option>ESD</option><option>ASD</option>
      <option>EPD</option><option>DAI</option><option>SMT</option>
    </select>
    <select id="fNat" onchange="filterTable()">
      <option value="">All Nationalities</option>
      <option>Singaporean</option><option>PR</option><option>International</option>
    </select>
  </div>
  <div id="count"></div>
  <table id="mainTable">
    <thead>
      <tr>
        <th>User</th><th>Status</th><th>Pillar</th>
        <th>Scholarship</th><th>Nationality</th><th>Text Snippet</th><th>Source</th>
      </tr>
    </thead>
    <tbody id="tbody">
      {_table_rows(records)}
    </tbody>
  </table>
</div>

<script>
const ALL = {records_json};
const STATUS_COLORS = {json.dumps(STATUS_COLORS)};

function pill(status) {{
  const c = STATUS_COLORS[status] || '#94a3b8';
  return `<span class="pill" style="background:${{c}}">${{status || '—'}}</span>`;
}}

function renderRows(data) {{
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = data.map(r => `
    <tr>
      <td>${{r.user_id || '—'}}</td>
      <td>${{pill(r.status)}}</td>
      <td>${{r.pillar || '—'}}</td>
      <td>${{r.scholarship || '—'}}</td>
      <td>${{r.nationality || '—'}}</td>
      <td class="snippet">${{r.text_snippet || ''}}</td>
      <td>${{r.post_url ? `<a href="${{r.post_url}}" target="_blank">view</a>` : '—'}}</td>
    </tr>`).join('');
  document.getElementById('count').textContent = `Showing ${{data.length}} of ${{ALL.length}} records`;
}}

function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const st = document.getElementById('fStatus').value;
  const pl = document.getElementById('fPillar').value;
  const nt = document.getElementById('fNat').value;
  const filtered = ALL.filter(r => {{
    const text = ((r.user_id||'') + ' ' + (r.text_snippet||'')).toLowerCase();
    return (!q || text.includes(q))
      && (!st || r.status === st)
      && (!pl || r.pillar === pl)
      && (!nt || r.nationality === nt);
  }});
  renderRows(filtered);
}}

renderRows(ALL);
</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report saved: {output_path}")
