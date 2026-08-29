#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build index.html from README.zh.md (Nolan180940 GitHub profile).

Usage:
    python scripts/build.py            # fetch README from GitHub, write index.html
    python scripts/build.py --local    # use local README.zh.md
    python scripts/build.py --out out.html
"""

import argparse
import datetime
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README_LOCAL = ROOT / "README.zh.md"
README_URL = "https://raw.githubusercontent.com/Nolan180940/Nolan180940/main/README.zh.md"
OUTPUT = ROOT / "index.html"

# ────────────────────────── Markdown helpers ──────────────────────────


def inline(md: str) -> str:
    """Convert inline markdown (bold/italic/code/image/link) to HTML.
    Raw HTML passes through untouched."""
    md = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", md)
    md = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", md)
    md = re.sub(r"`([^`]+)`", r"<code>\1</code>", md)
    md = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" loading="lazy" />', md)
    md = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', md)
    return md


def render_table(lines):
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
            continue  # separator row
        rows.append(cells)
    if not rows:
        return ""
    html = ['<div class="table-wrap"><table>']
    html.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead>")
    html.append("<tbody>")
    for row in rows[1:]:
        html.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


def render_list(lines):
    items = [inline(l.strip()[2:].strip()) for l in lines if l.strip().startswith("- ")]
    return "<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>"


def render_quote(lines):
    text = " ".join(l.strip()[1:].strip() for l in lines if l.strip().startswith(">"))
    return f"<blockquote>{inline(text)}</blockquote>"


def blocks(lines):
    """Convert markdown lines into HTML block elements."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i].strip()
        if not line or re.fullmatch(r"-{3,}|\*{3,}", line):
            i += 1
            continue
        if line.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            out.append(render_table(tbl))
            continue
        if line.startswith("> "):
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(lines[i].strip())
                i += 1
            out.append(render_quote(q))
            continue
        if line.startswith("- "):
            ul = []
            while i < n and lines[i].strip().startswith("- "):
                ul.append(lines[i].strip())
                i += 1
            out.append(render_list(ul))
            continue
        if line.startswith("<"):
            raw = []
            while i < n and lines[i].strip():
                raw.append(lines[i].rstrip())
                i += 1
            out.append("\n".join(inline(l) for l in raw))
            continue
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("- ", "> ", "|", "<")):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    return out


def strip_tag(html, tag):
    return re.sub(rf"</?{tag}>", "", html)


# ────────────────────────── Section renderers ──────────────────────────

ICONS = {"数据科学": "📊", "AI": "🤖", "量化金融": "📈"}


def render_hero(pre_lines):
    text = "\n".join(pre_lines)
    name = "Nolan Xu"
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if m:
        name = m.group(1).replace("你好，我是", "").replace("👋", "").strip() or name

    tagline = ""
    suffix = ""
    m = re.search(r"\*\*(.+?)\*\*\s*—\s*(.+)$", text, re.M)
    if m:
        tagline, suffix = m.group(1).strip(), m.group(2).strip()
    else:
        m = re.search(r"\*\*(.+?)\*\*", text)
        if m:
            tagline = m.group(1)
    tagline_html = f"<strong>{tagline}</strong> — {suffix}" if suffix else tagline

    degree = ""
    m = re.search(r"NYU '29 \|\s*(.+)$", text, re.M)
    if m:
        degree = m.group(1).strip()

    pills, seen = [], set()
    def add(p):
        if p not in seen:
            seen.add(p)
            pills.append(p)
    add("🎓 NYU '29")
    if degree:
        add("📊 " + degree)
    for part in tagline.split("×"):
        part = part.strip()
        if part:
            add(f"{ICONS.get(part, '✦')} {part}")
    add("🌏 上海")

    pill_html = "".join(
        f'<span class="pill pill-{"blue" if i % 3 == 0 else "teal" if i % 3 == 1 else "amber"}">{p}</span>'
        for i, p in enumerate(pills)
    )
    return f"""
  <section class="hero">
    <div class="hero-eyebrow">你好，我是</div>
    <h1 class="hero-name">{name}</h1>
    <p class="hero-tagline">{tagline_html}</p>
    <div class="hero-pills">{pill_html}</div>
  </section>"""


def render_about(lines):
    blocks_html = blocks(lines)
    intro, items = "", []
    for b in blocks_html:
        if b.startswith("<p"):
            intro = strip_tag(b, "p")
        elif b.startswith("<ul"):
            items = re.findall(r"<li>(.*?)</li>", b, re.S)
    html = ['<div class="cards cards-3">']
    html.append('<div class="card card-accent-blue card-span2">')
    html.append('<div class="card-icon">👨‍💻</div>')
    html.append(f'<div class="card-body">{intro}</div>')
    html.append("</div>")
    for it in items:
        html.append(f'<div class="card"><div class="card-body">{it}</div></div>')
    html.append("</div>")
    return "\n".join(html)


def render_stats(lines):
    blocks_html = blocks(lines)
    html = ['<div class="stats">']
    for b in blocks_html:
        html.append(b.replace('<div align="center">', '<div class="badges-row">'))
    html.append("</div>")
    return "\n".join(html)


def render_quant(lines):
    blocks_html = blocks(lines)
    quote_text, ul_html, callout = "", "", ""
    for b in blocks_html:
        if b.startswith("<blockquote"):
            text = strip_tag(b, "blockquote")
            if "📌" in text:
                callout = f'<div class="callout">{text}</div>'
            else:
                quote_text = text
        elif b.startswith("<ul"):
            ul_html = b
    html = ['<div class="cards">']
    html.append('<div class="card card-accent-blue">')
    html.append('<div class="card-icon">🔬</div>')
    html.append('<div class="card-body">')
    if quote_text:
        html.append(f"<p>{quote_text}</p>")
    if ul_html:
        html.append(ul_html)
    html.append("</div></div></div>")
    if callout:
        html.append(callout)
    return "\n".join(html)


def render_experience(lines):
    entries, cur = [], []
    for line in lines:
        if not line.strip():
            if cur:
                entries.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        entries.append(cur)
    html = []
    for entry in entries:
        title_line = entry[0].strip()
        date = ""
        m = re.search(r"`([^`]+)`", title_line)
        if m:
            date = m.group(1)
        title = inline(re.sub(r"`[^`]+`", "", title_line)).strip()
        html.append('<div class="exp-entry">')
        html.append(
            f'<div class="exp-head"><span class="exp-title">{title}</span>'
            f'<span class="exp-date">{date}</span></div>'
        )
        for b in blocks(entry[1:]):
            if b.startswith("<blockquote"):
                html.append(f'<div class="exp-note">{strip_tag(b, "blockquote")}</div>')
            else:
                html.append(b)
        html.append("</div>")
    return "".join(html)


def render_resume(lines):
    subs, current = {}, None
    for line in lines:
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            current = m.group(1).strip()
            subs[current] = []
        elif current is not None:
            subs[current].append(line)
    html = ['<div class="cards cards-2">']
    for title, sub_lines in subs.items():
        if title == "🧑‍💼 专业经历":
            body = render_experience(sub_lines)
            accent, span2 = "card-accent-blue", " card-span2"
        else:
            blocks_html = blocks(sub_lines)
            has_table = any("<table" in b for b in blocks_html)
            accent = {"🤖 竞赛与项目": "card-accent-teal", "🏅 教育背景": "card-accent-amber"}.get(title, "")
            span2 = " card-span2" if has_table else ""
            body_parts = []
            for b in blocks_html:
                if b.startswith("<p"):
                    body_parts.append(strip_tag(b, "p"))
                elif b.startswith("<ul"):
                    body_parts.append(b)
                elif "<table" in b:
                    body_parts.append(b)
                elif b.startswith("<blockquote"):
                    body_parts.append(f'<div class="exp-note">{strip_tag(b, "blockquote")}</div>')
            body = "\n".join(body_parts)
        html.append(f'<div class="card {accent}{span2}">'.replace("  ", " "))
        html.append(f'<div class="card-title">{title}</div>')
        html.append(f'<div class="card-body">{body}</div>')
        html.append("</div>")
    html.append("</div>")
    return "\n".join(html)


def render_pinned(lines):
    html = ['<div class="projects">']
    n = 0
    for line in lines:
        line = line.strip()
        if not line.startswith("- "):
            continue
        n += 1
        content = line[2:].strip()
        m = re.match(r"^(\S+?)\s+", content)
        icon = m.group(1) if m else "📦"
        m = re.search(r"\[(.+?)\]\((.+?)\)", content)
        if m:
            name, url = m.group(1).replace("**", ""), m.group(2)
        else:
            name, url = content, "#"
        desc = content.split("—", 1)[1].strip() if "—" in content else ""
        html.append(f'<a class="proj" href="{url}" target="_blank" rel="noopener">')
        html.append(f'<span class="proj-num">{n:02d}</span>')
        html.append(f'<span class="proj-icon">{icon}</span>')
        html.append(f'<span class="proj-name">{name}</span>')
        html.append(f'<span class="proj-desc">{inline(desc)}</span>')
        html.append('<span class="proj-arrow">→</span>')
        html.append("</a>")
    html.append("</div>")
    return "\n".join(html)


def render_repos(lines):
    blocks_html = blocks(lines)
    html = []
    for b in blocks_html:
        if b.startswith("<blockquote"):
            text = strip_tag(b, "blockquote")
            html.append(f'<div class="notice">{text}</div>' if "📌" in text else f'<div class="callout">{text}</div>')
        elif "<table" in b:
            html.append(b)
        elif b.startswith("<p"):
            html.append(f'<div class="notice">{strip_tag(b, "p")}</div>')
    return "\n".join(html)


def render_stack(lines):
    blocks_html = blocks(lines)
    html = []
    for b in blocks_html:
        if "<table" in b:
            html.append(b)
        elif b.startswith("<p") or b.startswith("<div"):
            html.append(f'<div class="stack-icons">{b}</div>')
    return "\n".join(html)


def render_philosophy(lines):
    text = " ".join(l.strip()[1:].strip() for l in lines if l.strip().startswith(">"))
    return f'<div class="philosophy"><p>{inline(text)}</p></div>'


def render_contact(lines):
    blocks_html = blocks(lines)
    badges, sub = "", ""
    for b in blocks_html:
        if b.startswith("<div") or b.startswith("<p"):
            badges = b.replace('<div align="center">', '<div class="badges-row">')
        elif b.startswith("<blockquote"):
            sub = strip_tag(b, "blockquote")
    email = "Alexander_123Wiggins@proton.me"
    m = re.search(r"mailto:([^\"')]+)", "\n".join(lines))
    if m:
        email = m.group(1)
    html = [f'<div class="contact-badges">{badges}</div>']
    html.append('<div class="contact-bar">')
    html.append("<div>")
    html.append('<div class="contact-heading">联系我 👋</div>')
    html.append(f'<div class="contact-sub">{sub}</div>')
    html.append("</div>")
    html.append(f'<a class="contact-btn" href="mailto:{email}"><span>📫</span> 发邮件</a>')
    html.append("</div>")
    return "\n".join(html)


# ────────────────────────── Page template ──────────────────────────

CSS = """
    :root {
      --cream:   #faf8f4;
      --white:   #ffffff;
      --ink:     #1c1c1e;
      --charcoal:#3a3a3c;
      --muted:   #8e8e93;
      --line:    #e5e2da;
      --blue:    #2563eb;
      --blue-lt: #eff4ff;
      --teal:    #0d9488;
      --teal-lt: #f0fdfb;
      --amber:   #d97706;
      --amber-lt:#fffbeb;
      --serif:   'Times New Roman', 'SimSun', 'Noto Serif SC', serif;
      --sans:    'Times New Roman', 'SimSun', 'Noto Serif SC', serif;
      --mono:    'Times New Roman', 'SimSun', 'Noto Serif SC', serif;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html { scroll-behavior: smooth; }

    body {
      background: var(--cream);
      color: var(--ink);
      font-family: var(--sans);
      font-size: 16px;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    .page { max-width: 780px; margin: 0 auto; padding: 0 24px 100px; }

    /* ── Hero ── */
    .hero {
      padding: 72px 0 52px;
      border-bottom: 1.5px solid var(--line);
      animation: rise 0.7s cubic-bezier(0.22,1,0.36,1) both;
    }
    @keyframes rise {
      from { opacity:0; transform:translateY(20px); }
      to   { opacity:1; transform:translateY(0); }
    }

    .hero-eyebrow {
      font-family: var(--mono);
      font-size: 0.72rem;
      letter-spacing: 0.13em;
      text-transform: uppercase;
      color: var(--blue);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .hero-eyebrow::before {
      content: '';
      display: inline-block;
      width: 28px; height: 1.5px;
      background: var(--blue);
    }

    .hero-name {
      font-family: var(--serif);
      font-size: clamp(2.8rem, 7vw, 4.4rem);
      line-height: 1.1;
      letter-spacing: -0.02em;
      margin-bottom: 18px;
    }
    .hero-name em { font-style: italic; color: var(--blue); }

    .hero-tagline {
      font-size: 1.05rem;
      color: var(--charcoal);
      font-weight: 300;
      margin-bottom: 30px;
      max-width: 520px;
      line-height: 1.7;
    }
    .hero-tagline strong { color: var(--ink); font-weight: 500; }

    .hero-pills { display: flex; flex-wrap: wrap; gap: 8px; }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 14px;
      border-radius: 100px;
      font-size: 0.78rem;
      font-weight: 500;
      border: 1px solid transparent;
    }
    .pill-blue  { background: var(--blue-lt);  color: var(--blue);  border-color: #bfcfff; }
    .pill-teal  { background: var(--teal-lt);  color: var(--teal);  border-color: #99e6de; }
    .pill-amber { background: var(--amber-lt); color: var(--amber); border-color: #fcd98a; }

    /* ── Sections ── */
    .section {
      padding: 52px 0 0;
      animation: rise 0.6s cubic-bezier(0.22,1,0.36,1) both;
    }
    .section:nth-child(2) { animation-delay: 0.05s; }
    .section:nth-child(3) { animation-delay: 0.10s; }
    .section:nth-child(4) { animation-delay: 0.15s; }
    .section:nth-child(5) { animation-delay: 0.20s; }
    .section:nth-child(6) { animation-delay: 0.25s; }
    .section:nth-child(7) { animation-delay: 0.30s; }
    .section:nth-child(8) { animation-delay: 0.35s; }
    .section:nth-child(9) { animation-delay: 0.40s; }
    .section:nth-child(10) { animation-delay: 0.45s; }

    .section-label {
      font-family: var(--mono);
      font-size: 0.68rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .section-label::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--line);
    }

    /* ── Cards ── */
    .cards { display: grid; gap: 14px; }
    .cards-2 { grid-template-columns: 1fr 1fr; }
    .cards-3 { grid-template-columns: repeat(3, 1fr); }
    .card {
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 22px 24px;
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .card:hover {
      box-shadow: 0 8px 30px rgba(0,0,0,0.07);
      transform: translateY(-2px);
    }
    .card-icon { font-size: 1.4rem; margin-bottom: 10px; }
    .card-title {
      font-family: var(--serif);
      font-size: 1.08rem;
      margin-bottom: 8px;
    }
    .card-body {
      font-size: 0.85rem;
      color: var(--charcoal);
      line-height: 1.7;
      font-weight: 300;
    }
    .card-body p { margin-bottom: 8px; }
    .card-body p:last-child { margin-bottom: 0; }
    .card-body ul { padding-left: 18px; margin-top: 8px; }
    .card-body li { margin: 4px 0; }
    .card-body strong { color: var(--ink); font-weight: 500; }
    .card-accent-blue  { border-top: 3px solid var(--blue); }
    .card-accent-teal  { border-top: 3px solid var(--teal); }
    .card-accent-amber { border-top: 3px solid var(--amber); }
    .card-span2 { grid-column: 1 / -1; }

    /* ── Experience entries ── */
    .exp-entry { padding: 14px 0; border-bottom: 1px dashed var(--line); }
    .exp-entry:first-child { padding-top: 0; }
    .exp-entry:last-child { border-bottom: none; padding-bottom: 0; }
    .exp-head {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 6px;
    }
    .exp-title { font-weight: 500; font-size: 0.92rem; color: var(--ink); }
    .exp-date {
      font-family: var(--mono);
      font-size: 0.7rem;
      color: var(--muted);
      white-space: nowrap;
    }
    .exp-note {
      font-size: 0.82rem;
      color: var(--charcoal);
      background: var(--teal-lt);
      border-left: 3px solid var(--teal);
      padding: 8px 12px;
      border-radius: 0 6px 6px 0;
      margin: 8px 0;
      font-weight: 300;
    }

    /* ── Tables ── */
    .table-wrap { overflow-x: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
    }
    th {
      text-align: left;
      font-family: var(--mono);
      font-size: 0.66rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      padding: 12px 14px;
      border-bottom: 1.5px solid var(--line);
      background: #f6f4ee;
      white-space: nowrap;
    }
    td {
      padding: 10px 14px;
      border-bottom: 1px solid var(--line);
      color: var(--charcoal);
      font-weight: 300;
      vertical-align: top;
    }
    tr:last-child td { border-bottom: none; }
    td a { color: var(--ink); font-weight: 500; text-decoration: none; }
    td a:hover { color: var(--blue); }
    td code { font-size: 0.8em; }

    /* ── Inline code ── */
    code {
      font-family: var(--mono);
      font-size: 0.85em;
      background: #f1efe9;
      padding: 2px 6px;
      border-radius: 4px;
      color: var(--charcoal);
    }

    /* ── Stats ── */
    .stats { display: flex; flex-direction: column; align-items: center; gap: 18px; }
    .stats img { max-width: 100%; height: auto; }
    .stats p { text-align: center; }
    .badges-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 8px; }

    /* ── Projects ── */
    .projects { display: flex; flex-direction: column; gap: 6px; }
    .proj {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 13px 18px;
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 10px;
      text-decoration: none;
      color: var(--ink);
      transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
    }
    .proj:hover {
      border-color: var(--blue);
      box-shadow: 0 4px 18px rgba(37,99,235,0.09);
      transform: translateX(4px);
    }
    .proj-num {
      font-family: var(--mono);
      font-size: 0.62rem;
      color: var(--muted);
      width: 20px;
      flex-shrink: 0;
    }
    .proj-icon { font-size: 1.05rem; flex-shrink: 0; }
    .proj-name { font-weight: 500; font-size: 0.88rem; flex: 1; }
    .proj-desc { font-size: 0.78rem; color: var(--muted); font-weight: 300; }
    .proj-arrow { color: var(--line); font-size: 0.85rem; transition: color 0.15s; flex-shrink: 0; }
    .proj:hover .proj-arrow { color: var(--blue); }

    .notice {
      margin-top: 12px;
      padding: 12px 18px;
      background: var(--blue-lt);
      border: 1px solid #bfcfff;
      border-radius: 8px;
      font-size: 0.82rem;
      color: var(--blue);
    }
    .notice strong { font-weight: 500; }

    /* ── Callout ── */
    .callout {
      border-left: 3px solid var(--amber);
      background: var(--amber-lt);
      padding: 14px 20px;
      border-radius: 0 8px 8px 0;
      font-size: 0.87rem;
      color: #92400e;
      font-style: italic;
      line-height: 1.7;
      margin-top: 16px;
    }

    /* ── Stack icons ── */
    .stack-icons {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      margin-bottom: 18px;
    }
    .stack-icons img { max-width: 100%; height: auto; }

    /* ── Philosophy ── */
    .philosophy {
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 28px 30px;
    }
    .philosophy p {
      font-size: 0.97rem;
      line-height: 1.82;
      color: var(--charcoal);
      font-weight: 300;
      margin-bottom: 14px;
    }
    .philosophy p:last-child { margin-bottom: 0; }
    .philosophy strong { color: var(--ink); font-weight: 500; }

    /* ── Contact ── */
    .contact-badges { margin-bottom: 28px; text-align: center; }
    .contact-badges img { max-width: 100%; height: auto; }
    .contact-bar {
      margin-top: 8px;
      padding: 30px 32px;
      background: var(--ink);
      border-radius: 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      flex-wrap: wrap;
    }
    .contact-heading {
      font-family: var(--serif);
      font-size: 1.4rem;
      color: var(--white);
      margin-bottom: 4px;
    }
    .contact-sub { font-size: 0.82rem; color: #8e8e93; font-weight: 300; }
    .contact-btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--white);
      color: var(--ink);
      text-decoration: none;
      padding: 11px 22px;
      border-radius: 100px;
      font-weight: 500;
      font-size: 0.88rem;
      transition: background 0.15s, transform 0.15s;
      white-space: nowrap;
    }
    .contact-btn:hover { background: #e8e8ec; transform: scale(1.03); }

    /* ── Footer note ── */
    .footer-note {
      margin-top: 28px;
      text-align: center;
      font-family: var(--mono);
      font-size: 0.66rem;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    .footer-note a { color: var(--muted); text-decoration: underline; }
    .footer-note a:hover { color: var(--blue); }

    @media (max-width: 580px) {
      .cards-2, .cards-3 { grid-template-columns: 1fr; }
      .card-span2 { grid-column: auto; }
      .proj-desc { display: none; }
      .contact-bar { flex-direction: column; align-items: flex-start; }
    }
"""


def render_page(hero_html, sections_html, date_str):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nolan Xu — 个人主页</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=DM+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;500;600&family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lxgw-wenkai-webfont@1.7.0/style.css">
  <style>{CSS}
  </style>
</head>
<body>
<div class="page">

{hero_html}
{sections_html}

  <div class="footer-note">
    由 <a href="https://github.com/Nolan180940/Nolan180940" target="_blank" rel="noopener">README.zh.md</a> 自动生成 · 最后同步 {date_str}
  </div>

</div>
</body>
</html>
"""


# ────────────────────────── Main ──────────────────────────


def fetch_readme() -> str:
    req = urllib.request.Request(README_URL, headers={"User-Agent": "about-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Build index.html from README.zh.md")
    parser.add_argument("--local", action="store_true", help="use local README.zh.md instead of fetching from GitHub")
    parser.add_argument("--out", default=str(OUTPUT), help="output file path")
    args = parser.parse_args()

    if args.local:
        md = README_LOCAL.read_text(encoding="utf-8")
        print(f"[build] reading local {README_LOCAL}")
    else:
        try:
            md = fetch_readme()
            print(f"[build] fetched {README_URL}")
        except Exception as e:
            print(f"[build] fetch failed ({e}), falling back to local README.zh.md", file=sys.stderr)
            if not README_LOCAL.exists():
                sys.exit(f"[build] error: no local README.zh.md and fetch failed: {e}")
            md = README_LOCAL.read_text(encoding="utf-8")

    # split hero (before first ##) and sections
    lines = md.splitlines()
    hero_lines, sections = [], {}
    current = None
    for line in lines:
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            current = m.group(1).strip()
            sections[current] = []
        elif current is None:
            hero_lines.append(line)
        else:
            sections[current].append(line)

    renderers = {
        "👨‍💻 关于我": render_about,
        "📊 Stats & Activity": render_stats,
        "🔬 量化研究 · 当前重点项目": render_quant,
        "🎯 简历一览": render_resume,
        "📌 主页精选项目（Pinned）": render_pinned,
        "🔥 最近更新 · Top 15 仓库": render_repos,
        "🛠️ 技术栈": render_stack,
        "💭 理念": render_philosophy,
        "📬 联系我": render_contact,
    }

    hero_html = render_hero(hero_lines)
    sections_html = []
    for title, body_lines in sections.items():
        renderer = renderers.get(title)
        if renderer is None:
            print(f"[build] warning: no renderer for section '{title}', skipping", file=sys.stderr)
            continue
        sections_html.append(f'  <section class="section">\n    <div class="section-label">{title}</div>\n{renderer(body_lines)}\n  </section>')
    sections_html = "\n".join(sections_html)

    date_str = datetime.date.today().isoformat()
    html = render_page(hero_html, sections_html, date_str)

    out = Path(args.out)
    out.write_text(html, encoding="utf-8")
    print(f"[build] wrote {out} ({len(html)} bytes, {len(sections)} sections)")


if __name__ == "__main__":
    main()