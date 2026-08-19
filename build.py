#!/usr/bin/env python3
"""
build.py — regenerate the project cards in index.html from projects.json

The cards between the PROJECTS:START / PROJECTS:END markers in index.html are
generated. Never edit them by hand — edit projects.json and run this instead.

Usage:
    python build.py              # regenerate cards
    python build.py --check      # verify index.html is up to date (exit 1 if not)
    python build.py --sync       # pull live stars/language from GitHub first
"""

import os
import re
import sys
import json
import html
import argparse
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(HERE, "index.html")
DATA_FILE = os.path.join(HERE, "projects.json")

START = "<!-- PROJECTS:START"
END = "<!-- PROJECTS:END -->"
GH_USER = "ABDULLAH-AMJID"

STAGGER = 0.06          # seconds between card reveal animations
WRAP_AT = 104           # soft wrap width for prose, keeps the HTML readable


class C:
    G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
    B = "\033[94m"; D = "\033[2m"; X = "\033[0m"; BD = "\033[1m"


def die(msg):
    print(f"{C.R}error:{C.X} {msg}")
    sys.exit(1)


# ──────────────────────────── rendering ────────────────────────────

def wrap(text, indent):
    """Soft-wrap prose so the generated HTML stays readable in a diff."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > WRAP_AT:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    pad = " " * indent
    return "\n".join(pad + l for l in lines)


def render_card(p, i):
    """Render one <article> exactly in the site's existing style."""
    style = "" if i == 0 else f' style="--rd:{round(i * STAGGER, 2)}s"'.replace("0.", ".")
    num = f"{i + 1:02d}"

    name = p["name"]
    url = p["url"]
    flag = p.get("flag", "")
    role = p.get("role", "")

    out = []
    out.append(f'        <article class="card reveal"{style}>')
    out.append(f'          <div class="card-num">{num}</div>')
    out.append(f'          <div>')
    out.append(f'            <div class="card-top">')
    out.append(f'              <h3><a href="{url}" target="_blank" rel="noopener">'
               f'{name} <span class="arrow">↗</span></a></h3>')
    if flag:
        out.append(f'              <span class="flag">{flag}</span>')
    out.append(f'            </div>')
    if role:
        out.append(f'            <div class="role">{role}</div>')
    if p.get("summary"):
        out.append(f'            <p>')
        out.append(wrap(p["summary"], 14))
        out.append(f'            </p>')
    if p.get("detail"):
        out.append(f'            <p class="detail">')
        out.append(wrap(p["detail"], 14))
        out.append(f'            </p>')
    if p.get("tags"):
        out.append(f'            <div class="tags">')
        line, chunks = "", []
        for t in p["tags"]:
            span = f'<span class="tag">{t}</span>'
            if line and len(line) + len(span) > 96:
                chunks.append(line)
                line = span
            else:
                line += span
        if line:
            chunks.append(line)
        for ch in chunks:
            out.append(f'              {ch}')
        out.append(f'            </div>')
    out.append(f'          </div>')
    out.append(f'        </article>')
    return "\n".join(out)


def render_all(projects):
    cards = [render_card(p, i) for i, p in enumerate(projects)]
    return "\n\n".join(cards)


# ──────────────────────────── github sync ────────────────────────────

def gh(path):
    url = f"https://api.github.com{path}"
    r = urllib.request.Request(url)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "portfolio-build")
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:
        r.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def sync(projects):
    """Refresh live metadata (stars, language, archived) from the GitHub API."""
    print(f"{C.B}Syncing metadata from GitHub…{C.X}")
    changed = 0
    for p in projects:
        m = re.search(r"github\.com/([^/]+)/([^/#?]+)", p.get("url", ""))
        if not m:
            continue
        owner, repo = m.group(1), m.group(2).rstrip("/")
        d = gh(f"/repos/{owner}/{repo}")
        if not d:
            print(f"  {C.Y}?{C.X} {repo} — could not fetch")
            continue
        live = {
            "stars": d.get("stargazers_count", 0),
            "language": d.get("language"),
            "archived": d.get("archived", False),
            "updated": (d.get("pushed_at") or "")[:10],
        }
        if p.get("_live") != live:
            p["_live"] = live
            changed += 1
        flags = []
        if live["archived"]:
            flags.append("archived")
        if live["stars"]:
            flags.append(f"{live['stars']}★")
        suffix = f"  {C.D}({', '.join(flags)}){C.X}" if flags else ""
        print(f"  {C.G}✓{C.X} {repo}{suffix}")
    print(f"{C.D}  {changed} record(s) updated{C.X}\n")
    return projects


# ──────────────────────────── main ────────────────────────────

def load():
    if not os.path.exists(DATA_FILE):
        die(f"{DATA_FILE} not found")
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    projects = data.get("projects", [])
    if not projects:
        die("projects.json contains no projects")
    for i, p in enumerate(projects):
        for field in ("name", "url"):
            if not p.get(field):
                die(f"project #{i + 1} is missing required field '{field}'")
    return data, projects


def splice(new_block):
    with open(HTML_FILE, encoding="utf-8") as f:
        src = f.read()
    si = src.find(START)
    ei = src.find(END)
    if si == -1 or ei == -1:
        die("PROJECTS:START / PROJECTS:END markers not found in index.html")
    line_end = src.index("\n", si)
    head = src[:line_end + 1]
    tail = src[ei:]
    return head + new_block + "\n        " + tail, src


def main():
    ap = argparse.ArgumentParser(description="Rebuild portfolio project cards")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if index.html is out of date (for CI)")
    ap.add_argument("--sync", action="store_true",
                    help="refresh stars/language from the GitHub API first")
    args = ap.parse_args()

    data, projects = load()

    if args.sync and not args.check:
        sync(projects)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    block = render_all(projects)
    out, old = splice(block)

    if args.check:
        if out != old:
            print(f"{C.R}✗ index.html is out of date — run: python build.py{C.X}")
            sys.exit(1)
        print(f"{C.G}✓ index.html is up to date{C.X}")
        return

    if out == old:
        print(f"{C.D}– no changes ({len(projects)} projects){C.X}")
        return

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"{C.G}✓ rebuilt {len(projects)} project cards{C.X}")
    for i, p in enumerate(projects):
        live = p.get("_live") or {}
        bits = []
        if live.get("stars"):
            bits.append(f"{live['stars']}★")
        if live.get("language"):
            bits.append(live["language"])
        meta = f"  {C.D}{' · '.join(bits)}{C.X}" if bits else ""
        print(f"  {C.D}{i + 1:02d}{C.X}  {p['name']}{meta}")


if __name__ == "__main__":
    main()
