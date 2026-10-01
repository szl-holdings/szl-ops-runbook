#!/usr/bin/env python3
"""Build the SZL ops runbook: markdown entries, search index, static site, PowerShell finder.

Usage: python tools/build.py
Outputs:
  runbook/<id>.md      one file per entry (front matter + sections)
  site/runbook.json    search index consumed by site/index.html and tools/Find-Fix.ps1
  site/index.html      searchable single-page runbook (no network dependencies)
  INDEX.md             table of every entry
"""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import entries_a, entries_b, entries_c  # noqa: E402

ENTRIES = entries_a.ENTRIES + entries_b.ENTRIES + entries_c.ENTRIES
TODAY = "2026-10-01"
E = html.escape

SURFACE_ORDER = ["github", "huggingface", "domains", "own-metal", "models", "local"]


def md_entry(e: dict) -> str:
    fm = [
        "---",
        f"id: {e['id']}",
        f"title: {json.dumps(e['title'], ensure_ascii=False)}",
        f"surface: {e['surface']}",
        f"severity: {e['severity']}",
        f"tags: [{', '.join(e['tags'])}]",
        f"last_verified: {TODAY}",
        "---",
    ]
    body = [
        f"# {e['title']}",
        "",
        "## Symptom",
        e["symptom"],
        "",
        "## Diagnose (PowerShell 5.1)",
        "```powershell",
        e["diagnose"].strip(),
        "```",
        "",
        "## Fix",
        "```powershell",
        e["fix"].strip(),
        "```",
        "",
        "## Verify",
        "```powershell",
        e["verify"].strip(),
        "```",
        "",
        "## Notes",
        e["notes"],
    ]
    if e.get("sources"):
        body += ["", "## Sources"] + [f"- {s}" for s in e["sources"]]
    return "\n".join(fm + body) + "\n"


def build_index_md() -> str:
    rows = ["# SZL ops runbook — index", "", f"{len(ENTRIES)} entries · last verified {TODAY}", "",
            "| id | surface | severity | title |", "|---|---|---|---|"]
    for e in sorted(ENTRIES, key=lambda x: (SURFACE_ORDER.index(x["surface"]), x["id"])):
        rows.append(f"| [`{e['id']}`](runbook/{e['id']}.md) | {e['surface']} | {e['severity']} | {e['title']} |")
    return "\n".join(rows) + "\n"


SITE_CSS = """
:root{--bg:#030F29;--deep:#02091c;--surface:#0b1630;--alt:#0f1c3a;--border:rgba(154,167,189,.16);--hair:rgba(154,167,189,.3);--text:#e9eef6;--sub:#b7c2d6;--ghost:#76859b;--accent:#DF735F;--link:#8fd9d5;--gold:#d7b96b;--ok:#3fce82;--warn:#e4cf99;--bad:#f0a3a3;--mono:ui-monospace,'Cascadia Code','JetBrains Mono',Menlo,Consolas,monospace;--body:system-ui,-apple-system,'Segoe UI',sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:var(--body);font-size:15px;line-height:1.55}
a{color:var(--link)}code,pre,kbd{font-family:var(--mono)}
header{position:sticky;top:0;z-index:5;background:rgba(3,15,41,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.bar{display:flex;gap:14px;align-items:center;height:64px}
.bar .brand{display:flex;align-items:center;gap:10px;font-weight:700;white-space:nowrap}.bar .brand svg{width:26px;height:26px}
.bar .brand small{color:var(--ghost);font-weight:500;font-family:var(--mono);font-size:11px;letter-spacing:.08em}
#q{flex:1;min-width:0;background:var(--deep);border:1px solid var(--hair);color:var(--text);border-radius:8px;padding:10px 14px;font-size:15px;font-family:var(--body)}
#q:focus{outline:3px solid #34aaa4;outline-offset:2px}
.hint{color:var(--ghost);font-size:12px;font-family:var(--mono);white-space:nowrap}
.filters{display:flex;gap:6px;flex-wrap:wrap;padding:10px 0 12px}
.f{border:1px solid var(--border);background:transparent;color:var(--sub);border-radius:999px;padding:4px 10px;font-size:12px;font-family:var(--mono);cursor:pointer}
.f.on{border-color:var(--accent);color:var(--text)}
main{display:grid;grid-template-columns:340px minmax(0,1fr);gap:18px;padding:18px 0 60px}
@media(max-width:900px){main{grid-template-columns:1fr}}
#list{display:flex;flex-direction:column;gap:6px;max-height:calc(100vh - 170px);overflow:auto;position:sticky;top:140px}
.item{border:1px solid var(--border);border-radius:8px;padding:10px 12px;background:var(--surface);cursor:pointer}
.item:hover,.item.sel{border-color:var(--hair);background:var(--alt)}
.item .t{font-weight:600;font-size:14px}.item .m{display:flex;gap:8px;color:var(--ghost);font-size:11px;font-family:var(--mono);margin-top:4px;flex-wrap:wrap}
.sev-high{color:var(--bad)}.sev-medium{color:var(--warn)}.sev-low{color:var(--ok)}
#view{min-width:0}
article{border:1px solid var(--border);border-radius:12px;background:var(--surface);padding:22px 24px}
article h1{font-size:22px;margin:0 0 6px;letter-spacing:-.01em}
article .meta{display:flex;gap:10px;flex-wrap:wrap;color:var(--ghost);font-family:var(--mono);font-size:12px;margin-bottom:16px}
article h2{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--ghost);font-family:var(--mono);margin:22px 0 8px}
article p{color:var(--sub);margin:0}
pre{position:relative;margin:0;background:var(--deep);border:1px solid var(--border);border-radius:8px;padding:14px 16px;overflow:auto;font-size:12.5px;line-height:1.5;color:var(--text);white-space:pre}
.copy{position:absolute;top:8px;right:8px;background:var(--alt);border:1px solid var(--hair);color:var(--sub);border-radius:6px;font:12px var(--mono);padding:4px 8px;cursor:pointer}
.copy:hover{color:var(--text)}.copy.done{color:var(--ok)}
.src a{display:block;font-size:12px;font-family:var(--mono);word-break:break-all}
.empty{color:var(--ghost);padding:40px;text-align:center;border:1px dashed var(--border);border-radius:12px}
.gold{border-left:3px solid var(--gold);padding-left:12px}
mark{background:rgba(223,115,95,.3);color:var(--text);border-radius:2px}
footer{color:var(--ghost);font-size:12px;font-family:var(--mono);padding:10px 0 30px;border-top:1px solid var(--border)}
"""

LOGO = ('<svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#0a0f1e"/>'
        '<path d="M32 12 L14 54" fill="none" stroke="#d7b96b" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M32 12 L50 54" fill="none" stroke="#5cc4bf" stroke-width="7" stroke-linecap="round"/>'
        '<g fill="#c0392b"><circle cx="40" cy="28" r="4"/><circle cx="44" cy="40" r="4"/><circle cx="48" cy="51" r="4"/></g></svg>')

SITE_JS = r"""
const DATA = window.__RUNBOOK__;
const $ = (s) => document.querySelector(s);
const list = $('#list'), view = $('#view'), q = $('#q');
let surface = 'all', sel = null;
const norm = (s) => (s || '').toLowerCase();
function score(e, terms) {
  if (!terms.length) return 1;
  const hay = norm([e.id, e.title, e.symptom, e.tags.join(' '), e.notes, e.diagnose, e.fix].join(' \n '));
  let s = 0;
  for (const t of terms) {
    if (!hay.includes(t)) return 0;
    s += norm(e.title).includes(t) ? 5 : 0;
    s += e.tags.some(x => norm(x).includes(t)) ? 3 : 0;
    s += norm(e.id).includes(t) ? 4 : 1;
  }
  return s;
}
function hi(text, terms) {
  let out = text.replace(/&/g,'&amp;').replace(/</g,'&lt;');
  for (const t of terms) { if (t.length < 2) continue; out = out.replace(new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&') + ')','gi'), '<mark>$1</mark>'); }
  return out;
}
function render() {
  const terms = norm(q.value).split(/\s+/).filter(Boolean);
  const rows = DATA.entries.map(e => ({e, s: score(e, terms)})).filter(r => r.s > 0 && (surface === 'all' || r.e.surface === surface)).sort((a,b) => b.s - a.s || a.e.title.localeCompare(b.e.title));
  list.innerHTML = rows.map(({e}) => `<div class="item${sel === e.id ? ' sel' : ''}" data-id="${e.id}"><div class="t">${hi(e.title, terms)}</div><div class="m"><span>${e.surface}</span><span class="sev-${e.severity}">${e.severity}</span><span>${e.id}</span></div></div>`).join('') || '<div class="empty">No entry matches. Try a symptom word: 530, 400, BEHIND, provenance, CONFIG_ERROR.</div>';
  $('#count').textContent = rows.length + ' / ' + DATA.entries.length;
  if (rows.length && (!sel || !rows.some(r => r.e.id === sel))) { sel = rows[0].e.id; }
  if (!rows.length) { sel = null; view.innerHTML = ''; return; }
  show(sel, terms);
}
function block(label, code) {
  return `<h2>${label}</h2><pre><button class="copy" data-code="${code.replace(/"/g,'&quot;')}">copy</button>${code.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</pre>`;
}
function show(id, terms) {
  const e = DATA.entries.find(x => x.id === id); if (!e) return;
  document.querySelectorAll('.item').forEach(i => i.classList.toggle('sel', i.dataset.id === id));
  location.hash = id;
  view.innerHTML = `<article>
    <h1>${hi(e.title, terms)}</h1>
    <div class="meta"><span>${e.surface}</span><span class="sev-${e.severity}">${e.severity}</span><span>last verified ${e.last_verified}</span><span>${e.tags.map(t => '#' + t).join(' ')}</span></div>
    <h2>Symptom</h2><p>${hi(e.symptom, terms)}</p>
    ${block('Diagnose · PowerShell 5.1', e.diagnose)}
    ${block('Fix', e.fix)}
    ${block('Verify', e.verify)}
    <h2>Notes</h2><p class="gold">${hi(e.notes, terms)}</p>
    ${e.sources.length ? '<h2>Sources</h2><div class="src">' + e.sources.map(s => `<a href="${s}" target="_blank" rel="noopener">${s}</a>`).join('') + '</div>' : ''}
  </article>`;
}
list.addEventListener('click', (ev) => { const it = ev.target.closest('.item'); if (it) { sel = it.dataset.id; show(sel, norm(q.value).split(/\s+/).filter(Boolean)); } });
view.addEventListener('click', async (ev) => { const b = ev.target.closest('.copy'); if (!b) return; try { await navigator.clipboard.writeText(b.dataset.code); b.textContent = 'copied'; b.classList.add('done'); setTimeout(() => { b.textContent = 'copy'; b.classList.remove('done'); }, 1400); } catch { b.textContent = 'select+copy'; } });
q.addEventListener('input', render);
document.querySelectorAll('.f').forEach(f => f.addEventListener('click', () => { document.querySelectorAll('.f').forEach(x => x.classList.remove('on')); f.classList.add('on'); surface = f.dataset.s; render(); }));
window.addEventListener('keydown', (ev) => { if (ev.key === '/' && document.activeElement !== q) { ev.preventDefault(); q.focus(); q.select(); } if (ev.key === 'Escape') { q.value = ''; render(); } });
if (location.hash) { sel = location.hash.slice(1); }
render(); q.focus();
"""


def build_site(index: dict) -> str:
    filters = ''.join(f'<button class="f" data-s="{s}">{s}</button>' for s in SURFACE_ORDER)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SZL ops runbook — fixes one search away</title><meta name="robots" content="noindex,nofollow">
<link rel="icon" type="image/svg+xml" href="favicon.svg"><style>{SITE_CSS}</style></head>
<body><header><div class="wrap"><div class="bar"><div class="brand">{LOGO}<span>SZL ops runbook <small>PRIVATE · {len(index['entries'])} entries · {TODAY}</small></span></div>
<input id="q" type="search" placeholder="Type a symptom: 530, 400 Bad Request, BEHIND, provenance, CONFIG_ERROR, stale image…" autocomplete="off" spellcheck="false">
<span class="hint"><span id="count"></span> · press / to search</span></div>
<div class="filters"><button class="f on" data-s="all">all</button>{filters}</div></div></header>
<div class="wrap"><main><div id="list"></div><div id="view"></div></main>
<footer>Every block is Windows PowerShell 5.1, written to run in an elevated console without prior shell state. Tokens are read with Read-Host -AsSecureString and never echoed. Source of truth: github.com/szl-holdings/szl-ops-runbook (private).</footer></div>
<script>window.__RUNBOOK__ = {json.dumps(index)};</script><script>{SITE_JS}</script></body></html>"""


def main() -> None:
    (ROOT / "runbook").mkdir(exist_ok=True)
    (ROOT / "site").mkdir(exist_ok=True)
    ids = [e["id"] for e in ENTRIES]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for e in ENTRIES:
        e["last_verified"] = TODAY
        (ROOT / "runbook" / f"{e['id']}.md").write_text(md_entry(e))
    index = {"schema": "szl.ops-runbook-index/v1", "built": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "entries": ENTRIES}
    raw = json.dumps(index, indent=1, sort_keys=True)
    (ROOT / "site" / "runbook.json").write_text(raw)
    index["sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    (ROOT / "site" / "index.html").write_text(build_site(index))
    (ROOT / "INDEX.md").write_text(build_index_md())
    print(f"entries={len(ENTRIES)} index_sha256={index['sha256'][:16]}… site={ (ROOT/'site'/'index.html').stat().st_size } bytes")


if __name__ == "__main__":
    main()
