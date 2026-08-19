#!/usr/bin/env python3
"""
add.py — add a project to the portfolio in one command

Pulls what it can from the GitHub API, asks you only for the parts a machine
can't write well, appends to projects.json, and rebuilds index.html.

Usage:
    python add.py SpaceMedic-2           # fetch that repo, then prompt
    python add.py --list                 # show current projects and order
    python add.py --remove "Vortex"      # remove by name
    python add.py --move "Vortex" 2      # move to position 2
    python add.py --edit "Vortex"        # re-edit an existing entry
"""

import os
import re
import sys
import json
import argparse
import subprocess
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "projects.json")
GH_USER = "ABDULLAH-AMJID"


class C:
    G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"
    B = "\033[94m"; D = "\033[2m"; X = "\033[0m"; BD = "\033[1m"


# language → suggested category flag
FLAG_BY_LANG = {
    "C++": "Systems / C++", "C": "Systems / C", "C#": "Desktop / C#",
    "Rust": "Systems / Rust", "Go": "Backend / Go",
    "Python": "Tooling / Python", "TypeScript": "Web", "JavaScript": "Web",
    "Java": "Backend / Java", "Kotlin": "Mobile / Android",
    "Swift": "Mobile / iOS", "Dart": "Mobile / Flutter",
    "HTML": "Web", "Shell": "Tooling",
}

# topic slug → display tag
TAG_MAP = {
    "cpp": "C++", "csharp": "C#", "dotnet": ".NET", "wpf": "WPF",
    "python": "Python", "typescript": "TypeScript", "javascript": "JavaScript",
    "react": "React", "vite": "Vite", "tailwindcss": "Tailwind CSS",
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "docker": "Docker", "supabase": "Supabase", "capacitor": "Capacitor",
    "websocket": "WebSocket", "rest-api": "REST", "async": "Async",
    "directshow": "DirectShow", "win32": "Win32 API", "windows": "Windows API",
    "tkinter": "Tkinter", "sqlite": "SQLite", "postgresql": "PostgreSQL",
    "audioworklet": "AudioWorklet", "web-audio-api": "Web Audio API",
    "networking": "Networking", "real-time": "Real-time",
    "shared-memory": "Shared Memory IPC", "systems-programming": "Systems",
    "github-actions": "GitHub Actions", "deno": "Deno",
    "edge-functions": "Edge Functions", "shadcn-ui": "shadcn/ui",
    "machine-learning": "Machine Learning", "opencv": "OpenCV",
}


def load():
    if not os.path.exists(DATA_FILE):
        return {"projects": []}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def rebuild():
    print()
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=False)


def gh(path):
    r = urllib.request.Request(f"https://api.github.com{path}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "portfolio-add")
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:
        r.add_header("Authorization", f"Bearer {tok}")
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"{C.Y}  could not reach GitHub ({e}){C.X}")
        return None


def prettify(slug):
    """my-cool-repo → My Cool Repo"""
    words = re.split(r"[-_]+", slug)
    out = []
    for w in words:
        if w.isupper() or (len(w) > 1 and w[1:].islower() and w[0].isupper()):
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)


def ask(label, default="", hint="", multiline=False):
    if hint:
        print(f"{C.D}  {hint}{C.X}")
    shown = f" {C.D}[{default[:70]}{'…' if len(default) > 70 else ''}]{C.X}" if default else ""
    if multiline:
        print(f"{C.BD}{label}{C.X}{shown}  {C.D}(blank line to finish){C.X}")
        lines = []
        while True:
            try:
                line = input("  ")
            except EOFError:
                break
            if not line.strip():
                break
            lines.append(line.strip())
        val = " ".join(lines).strip()
    else:
        try:
            val = input(f"{C.BD}{label}{C.X}{shown}\n  ").strip()
        except EOFError:
            val = ""
    return val or default


def build_entry(repo_slug=None, existing=None):
    d = None
    if repo_slug:
        print(f"{C.B}Fetching {GH_USER}/{repo_slug}…{C.X}")
        d = gh(f"/repos/{GH_USER}/{repo_slug}")
        if d:
            langs = gh(f"/repos/{GH_USER}/{repo_slug}/languages") or {}
            print(f"{C.G}✓{C.X} found — {d.get('language') or '?'}"
                  f" · {d.get('stargazers_count', 0)}★"
                  f" · {len(d.get('topics') or [])} topics\n")
        else:
            print(f"{C.Y}!{C.X} repo not found — you can still enter it manually\n")
            langs = {}
    else:
        langs = {}

    e = dict(existing or {})

    # name
    default_name = e.get("name") or (prettify(repo_slug) if repo_slug else "")
    e["name"] = ask("Display name", default_name,
                    "How it should appear on the site — not the repo slug")

    # url
    default_url = e.get("url") or (f"https://github.com/{GH_USER}/{repo_slug}"
                                   if repo_slug else "")
    e["url"] = ask("Link", default_url)

    # flag
    lang = (d or {}).get("language") or ""
    default_flag = e.get("flag") or FLAG_BY_LANG.get(lang, "")
    print(f"{C.D}  e.g. Systems / C++ · Desktop / Safety-critical · "
          f"Real-time audio · Backend / DevOps{C.X}")
    e["flag"] = ask("Category badge", default_flag)

    # role
    e["role"] = ask("One-line subtitle", e.get("role", ""),
                    "Sits under the title. e.g. 'Custom DirectShow driver · Windows kernel-adjacent'")

    # summary
    default_sum = e.get("summary") or (d or {}).get("description") or ""
    default_sum = re.sub(r"\s+", " ", default_sum).strip()
    print(f"\n{C.D}  What it does and who it's for. Wrap the key phrase in "
          f"<strong>…</strong>.{C.X}")
    e["summary"] = ask("Summary paragraph", default_sum, multiline=True)

    # detail
    print(f"\n{C.D}  The interesting part — how you built it, what was hard.\n"
          f"  This is what makes a reviewer stop scrolling. Leave blank to skip.{C.X}")
    e["detail"] = ask("Technical detail", e.get("detail", ""), multiline=True)

    # tags
    suggested = []
    for t in ((d or {}).get("topics") or []):
        if t in TAG_MAP:
            suggested.append(TAG_MAP[t])
    for l in list(langs)[:3]:
        if l not in suggested:
            suggested.append(l)
    seen, uniq = set(), []
    for t in suggested:
        if t.lower() not in seen:
            seen.add(t.lower())
            uniq.append(t)
    default_tags = ", ".join(e.get("tags") or uniq[:6])
    print(f"\n{C.D}  Comma separated. 4–6 works best.{C.X}")
    raw = ask("Tech tags", default_tags)
    e["tags"] = [t.strip() for t in raw.split(",") if t.strip()]

    if d:
        e["_live"] = {
            "stars": d.get("stargazers_count", 0),
            "language": d.get("language"),
            "archived": d.get("archived", False),
            "updated": (d.get("pushed_at") or "")[:10],
        }
    return e


def show_list(projects):
    if not projects:
        print(f"{C.D}no projects yet{C.X}")
        return
    print(f"\n{C.BD}Current order{C.X}  {C.D}(top = strongest, shown first){C.X}\n")
    for i, p in enumerate(projects):
        live = p.get("_live") or {}
        bits = []
        if live.get("language"):
            bits.append(live["language"])
        if live.get("stars"):
            bits.append(f"{live['stars']}★")
        if live.get("archived"):
            bits.append("archived")
        meta = f"  {C.D}{' · '.join(bits)}{C.X}" if bits else ""
        print(f"  {C.D}{i + 1:02d}{C.X}  {C.BD}{p['name']}{C.X}{meta}")
        if p.get("flag"):
            print(f"      {C.D}{p['flag']}{C.X}")
    print()


def find(projects, name):
    for i, p in enumerate(projects):
        if p["name"].lower() == name.lower():
            return i
    for i, p in enumerate(projects):
        if name.lower() in p["name"].lower():
            return i
    return -1


def main():
    ap = argparse.ArgumentParser(description="Add or manage portfolio projects")
    ap.add_argument("repo", nargs="?", help="GitHub repo name to import")
    ap.add_argument("--list", action="store_true", help="list current projects")
    ap.add_argument("--remove", metavar="NAME", help="remove a project")
    ap.add_argument("--edit", metavar="NAME", help="re-edit a project")
    ap.add_argument("--move", nargs=2, metavar=("NAME", "POS"),
                    help="move a project to position POS (1-based)")
    ap.add_argument("--top", metavar="NAME", help="move a project to position 1")
    args = ap.parse_args()

    data = load()
    projects = data.setdefault("projects", [])

    if args.list:
        show_list(projects)
        return

    if args.remove:
        i = find(projects, args.remove)
        if i < 0:
            print(f"{C.R}not found:{C.X} {args.remove}")
            sys.exit(1)
        gone = projects.pop(i)
        save(data)
        print(f"{C.G}✓ removed{C.X} {gone['name']}")
        rebuild()
        return

    if args.top or args.move:
        name = args.top or args.move[0]
        pos = 1 if args.top else int(args.move[1])
        i = find(projects, name)
        if i < 0:
            print(f"{C.R}not found:{C.X} {name}")
            sys.exit(1)
        p = projects.pop(i)
        projects.insert(max(0, min(pos - 1, len(projects))), p)
        save(data)
        print(f"{C.G}✓ moved{C.X} {p['name']} → position {pos}")
        show_list(projects)
        rebuild()
        return

    if args.edit:
        i = find(projects, args.edit)
        if i < 0:
            print(f"{C.R}not found:{C.X} {args.edit}")
            sys.exit(1)
        print(f"{C.BD}Editing {projects[i]['name']}{C.X}  "
              f"{C.D}press Enter to keep each value{C.X}\n")
        projects[i] = build_entry(existing=projects[i])
        save(data)
        print(f"\n{C.G}✓ updated{C.X}")
        rebuild()
        return

    # add flow
    if not args.repo:
        print(f"{C.BD}Add a project{C.X}  {C.D}(no repo given — manual entry){C.X}\n")
    entry = build_entry(repo_slug=args.repo)

    if not entry.get("name") or not entry.get("url"):
        print(f"{C.R}name and link are required — nothing saved{C.X}")
        sys.exit(1)

    i = find(projects, entry["name"])
    if i >= 0:
        projects[i] = entry
        print(f"\n{C.G}✓ replaced existing entry{C.X}")
    else:
        print(f"\n{C.D}Where should it go? 1 = top. "
              f"Blank = end (position {len(projects) + 1}).{C.X}")
        try:
            pos = input(f"{C.BD}Position{C.X}\n  ").strip()
        except EOFError:
            pos = ""
        if pos.isdigit():
            projects.insert(max(0, min(int(pos) - 1, len(projects))), entry)
        else:
            projects.append(entry)
        print(f"\n{C.G}✓ added{C.X} {entry['name']}")

    save(data)
    show_list(projects)
    rebuild()


if __name__ == "__main__":
    main()
