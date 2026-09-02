#!/usr/bin/env python3

import html
import json
import os
import re
import urllib.parse
import urllib.request

USER = "ABDULLAH-AMJID"
PORTFOLIO_REPO = f"{USER}.github.io".lower()
DATA_FILE = "projects.json"

FLAG_BY_LANGUAGE = {
    "C++": "Systems / C++",
    "C": "Systems / C",
    "C#": "Desktop / C#",
    "Rust": "Systems / Rust",
    "Go": "Backend / Go",
    "Python": "Tooling / Python",
    "TypeScript": "Web / TypeScript",
    "JavaScript": "Web / JavaScript",
    "Java": "Backend / Java",
    "Kotlin": "Mobile / Android",
    "Swift": "Mobile / iOS",
    "Dart": "Mobile / Flutter",
    "HTML": "Web",
    "Shell": "Tooling",
}

TAG_BY_TOPIC = {
    "cpp": "C++",
    "csharp": "C#",
    "dotnet": ".NET",
    "wpf": "WPF",
    "python": "Python",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "react": "React",
    "vite": "Vite",
    "tailwindcss": "Tailwind CSS",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "docker": "Docker",
    "supabase": "Supabase",
    "capacitor": "Capacitor",
    "websocket": "WebSocket",
    "rest-api": "REST",
    "async": "Async",
    "directshow": "DirectShow",
    "win32": "Win32 API",
    "windows": "Windows API",
    "tkinter": "Tkinter",
    "sqlite": "SQLite",
    "audioworklet": "AudioWorklet",
    "web-audio-api": "Web Audio API",
    "networking": "Networking",
    "real-time": "Real-time",
    "shared-memory": "Shared Memory IPC",
    "github-actions": "GitHub Actions",
}


def github_api(path, params=None):
    url = "https://api.github.com" + path

    if params:
        url += "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "abdullah-amjid-portfolio-sync",
        },
    )

    token = os.environ.get("GITHUB_TOKEN", "").strip()

    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def repo_key(value):
    if isinstance(value, dict):
        value = value.get("full_name", "")

    value = str(value).strip()

    if re.fullmatch(r"[^/]+/[^/#?]+", value):
        return value.lower()

    match = re.search(r"github\.com/([^/]+)/([^/#?]+)", value)

    if not match:
        return ""

    return f"{match.group(1)}/{match.group(2)}".lower()


def get_all_repositories():
    repositories = []
    page = 1

    while True:
        batch = github_api(
            f"/users/{USER}/repos",
            {
                "type": "owner",
                "sort": "pushed",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
        )

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return repositories


def auto_tags(repository):
    tags = []
    language = repository.get("language")

    if language:
        tags.append(language)

    for topic in repository.get("topics") or []:
        tag = TAG_BY_TOPIC.get(
            topic,
            topic.replace("-", " ").title(),
        )

        if tag.lower() not in {item.lower() for item in tags}:
            tags.append(tag)

    return tags[:6]


def make_project(repository, previous=None):
    previous = dict(previous or {})
    language = repository.get("language") or ""

    description = " ".join(
        (repository.get("description") or "").split()
    )

    if previous:
        project = previous
    else:
        project = {
            "name": repository["name"],
            "url": repository["html_url"],
            "flag": FLAG_BY_LANGUAGE.get(language, "Open source"),
            "role": f"{language or 'Software'} project",
            "summary": html.escape(
                description or "Open-source project on GitHub."
            ),
            "detail": "",
            "tags": auto_tags(repository),
        }

    # Always keep the repository link current.
    project["url"] = repository["html_url"]
    project.setdefault("name", repository["name"])

    # Give newly discovered repositories a description.
    if not project.get("summary"):
        project["summary"] = html.escape(
            description or "Open-source project on GitHub."
        )

    if not project.get("tags"):
        project["tags"] = auto_tags(repository)

    project["_live"] = {
        "stars": repository.get("stargazers_count", 0),
        "language": language or None,
        "archived": bool(repository.get("archived", False)),
        "updated": (repository.get("pushed_at") or "")[:10],
    }

    return project


def main():
    with open(DATA_FILE, encoding="utf-8") as file:
        old_projects = json.load(file).get("projects", [])

    repositories = get_all_repositories()

    public_repositories = {
        repo_key(repository): repository
        for repository in repositories
        if not repository.get("private")
        and not repository.get("fork")
        and repository.get("name", "").lower() != PORTFOLIO_REPO
    }

    if not public_repositories:
        raise RuntimeError(
            "GitHub returned no public repositories. "
            "Refusing to overwrite projects.json."
        )

    old_by_key = {
        repo_key(project.get("url", "")): project
        for project in old_projects
    }

    # Keep your manually selected projects at the top.
    existing_order = [
        repo_key(project.get("url", ""))
        for project in old_projects
    ]

    existing_order = [
        key for key in existing_order
        if key in public_repositories
    ]

    # Add newly discovered repositories after the existing projects.
    new_order = sorted(
        (
            key
            for key in public_repositories
            if key not in existing_order
        ),
        key=lambda key: public_repositories[key].get("pushed_at") or "",
        reverse=True,
    )

    ordered_keys = existing_order + new_order

    projects = [
        make_project(
            public_repositories[key],
            old_by_key.get(key),
        )
        for key in ordered_keys
    ]

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"projects": projects},
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    print(
        f"Synced {len(projects)} public repositories "
        f"into {DATA_FILE}"
    )


if __name__ == "__main__":
    main()