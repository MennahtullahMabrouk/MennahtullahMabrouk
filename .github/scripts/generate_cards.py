#!/usr/bin/env python3
"""Regenerate the data-driven profile cards from the GitHub API.

Outputs:
  assets/top-languages-mac.svg  - real top languages by bytes across public repos
  assets/stats-row.svg          - radar (static) + GitHub stats card (dynamic)

Usage:
  GH_TOKEN=<token> python3 .github/scripts/generate_cards.py
  python3 .github/scripts/generate_cards.py --mock --out /tmp/cards
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

GH_USER = os.environ.get("GH_USER", "MennahtullahMabrouk")
API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "assets")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "profile-card-updater",
}
_TOKEN = os.environ.get("GH_TOKEN", "").strip()
if _TOKEN:
    HEADERS["Authorization"] = f"Bearer {_TOKEN}"

MOCK_DATA = {
    "stars": 128,
    "commits": 1523,
    "prs": 96,
    "followers": 51,
    "lang_bytes": {
        "Python": 2450000,
        "Jupyter Notebook": 900000,
        "R": 600000,
        "C++": 300000,
        "HTML": 180000,
        "CSS": 120000,
        "JavaScript": 90000,
        "Shell": 70000,
        "TeX": 40000,
    },
}

LANG_COLORS = {
    "Python": "#C77DFF",
    "Jupyter Notebook": "#FFB7B2",
    "R": "#A855F7",
    "Shell": "#818CF8",
    "Bash": "#818CF8",
    "SQL": "#818CF8",
    "PLpgSQL": "#818CF8",
    "C": "#6366F1",
    "C++": "#7C3AED",
    "C#": "#60A5FA",
    "TypeScript": "#3B82F6",
    "JavaScript": "#FACC15",
    "HTML": "#72EFDD",
    "CSS": "#FF85A1",
    "TeX": "#22D3EE",
    "Java": "#F87171",
    "MATLAB": "#FDBA74",
    "Stata": "#2DD4BF",
    "Go": "#2DD4BF",
    "Rust": "#F87171",
    "PHP": "#818CF8",
    "Dart": "#60A5FA",
    "Kotlin": "#A855F7",
    "Swift": "#F87171",
    "Haskell": "#6366F1",
    "Ruby": "#F87171",
    "Lua": "#3B82F6",
    "Perl": "#F0ABFC",
    "Fortran": "#6366F1",
    "Verilog": "#818CF8",
    "VHDL": "#22D3EE",
    "SAS": "#22D3EE",
}
FALLBACK_COLORS = ["#C084FC", "#A855F7", "#818CF8", "#6366F1", "#F0ABFC", "#60A5FA"]


def api(path):
    req = urllib.request.Request(f"{API}{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.headers.get("Link", "")


def fetch_all_repos():
    repos = []
    page = 1
    while True:
        batch, link = api(f"/users/{GH_USER}/repos?per_page=100&page={page}&sort=updated")
        repos.extend(batch)
        if 'rel="next"' not in link or not batch:
            break
        page += 1
    return [r for r in repos if not r.get("fork")]


def fetch_languages(repo):
    try:
        langs, _ = api(f"/repos/{GH_USER}/{repo['name']}/languages")
        return langs
    except urllib.error.HTTPError:
        return {}


def fetch_author_commits(repo):
    try:
        _, link = api(f"/repos/{GH_USER}/{repo['name']}/commits?author={GH_USER}&per_page=1")
    except urllib.error.HTTPError:
        return 0
    match = re.search(r"[?&]page=(\d+)>;\s*rel=\"last\"", link or "")
    return int(match.group(1)) if match else 0


def collect():
    user, _ = api(f"/users/{GH_USER}")
    repos = fetch_all_repos()
    lang_bytes = {}
    for repo in repos:
        for name, bytes_count in fetch_languages(repo).items():
            lang_bytes[name] = lang_bytes.get(name, 0) + bytes_count
    total_commits = sum(fetch_author_commits(repo) for repo in repos)
    try:
        search, _ = api(f"/search/issues?q=author:{GH_USER}")
        pr_count = search.get("total_count", 0)
    except urllib.error.HTTPError:
        pr_count = 0
    return {
        "stars": sum(repo.get("stargazers_count", 0) for repo in repos),
        "commits": total_commits,
        "prs": pr_count,
        "followers": user.get("followers", 0),
        "lang_bytes": lang_bytes,
    }


def escape(text):
    return html.escape(str(text), quote=False)


def lang_color(name, index):
    return LANG_COLORS.get(name, FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def top_languages_svg(lang_bytes):
    total = sum(lang_bytes.values()) or 1
    ranked = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:5]
    rows = [(name, round(b * 100 / total), lang_color(name, i))
            for i, (name, b) in enumerate(ranked)]
    rows = [row for row in rows if row[1] >= 1]
    if not rows:
        rows = [("No public code data", 0, "#818CF8")]
    height = 40 * len(rows) + 70
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 {height}" width="100%" height="100%" '
        f'shape-rendering="crispEdges" role="img" aria-label="Top languages">',
        f'  <rect x="0" y="0" width="850" height="{height}" fill="#181124" />',
        f'  <rect x="2" y="2" width="846" height="{height - 4}" rx="8" fill="#181124" stroke="#3C2A58" stroke-width="2"/>',
        '  <path d="M 2 30 L 848 30" stroke="#3C2A58" stroke-width="1.5"/>',
        '  <circle cx="20" cy="16" r="4" fill="#FF5F56"/>',
        '  <circle cx="34" cy="16" r="4" fill="#FFBD2E"/>',
        '  <circle cx="48" cy="16" r="4" fill="#27C93F"/>',
        '  <text x="425" y="21" fill="#C084FC" font-family="\'Courier New\', monospace" font-size="12" '
        'font-weight="bold" text-anchor="middle">Top_Languages.app ｜ 使用言語</text>',
        '  <g font-family="\'Courier New\', monospace" font-size="13" font-weight="bold">',
    ]
    for i, (name, pct, color) in enumerate(rows):
        y = 68 + 40 * i
        display = name if len(name) <= 22 else name[:19] + "..."
        bar_width = max(4, int(round(610 * pct / 100))) if pct > 0 else 0
        lines.append(f'    <text x="40" y="{y}" fill="#DDD6FE">{escape(display)}</text>')
        lines.append(f'    <text x="810" y="{y}" fill="#F0ABFC" text-anchor="end">{pct}%</text>')
        lines.append(f'    <rect x="200" y="{y + 8}" width="610" height="10" fill="#231934" rx="3" />')
        if bar_width:
            lines.append(f'    <rect x="200" y="{y + 8}" width="{bar_width}" fill="{color}" height="10" rx="3" />')
        lines.append(
            f'    <rect x="200" y="{y + 8}" width="70" height="10" fill="#FFFFFF" opacity="0" rx="3">\n'
            f'      <animate attributeName="opacity" values="0;0.35;0.35;0" keyTimes="0;0.12;0.88;1" '
            f'dur="2.8s" begin="{0.7 + i * 0.4:.1f}s" repeatCount="indefinite" />\n'
            f'      <animateTransform attributeName="transform" type="translate" values="0 0;540 0;0 0" '
            f'keyTimes="0;0.5;1" dur="2.8s" begin="{0.7 + i * 0.4:.1f}s" repeatCount="indefinite" />\n'
            f'    </rect>'
        )
    lines.append('  </g>')
    lines.append('</svg>')
    return "\n".join(lines)


def stats_group(stats):
    rows = [
        ("Total Stars Earned:", f"&#9733; {stats['stars']:,}"),
        ("Total Commits:", f"{stats['commits']:,}"),
        ("PRs &amp; Issues:", f"{stats['prs']:,}"),
        ("Followers:", f"{stats['followers']:,}"),
    ]
    lines = [
        '  <g transform="translate(364,1) scale(1.27895)">',
        '    <rect width="380" height="280" fill="#181124" stroke="#5B4670" stroke-width="1.5" rx="6" />',
        '    <text x="20" y="35" fill="#C084FC" font-family="\'Courier New\', monospace" font-size="14" '
        'font-weight="bold">GitHub_Stats.app ｜ 統計データ</text>',
        '    <line x1="20" y1="48" x2="360" y2="48" stroke="#3D2B52" stroke-width="1" />',
    ]
    for i, (label, value) in enumerate(rows):
        y = 85 + 40 * i
        lines.append(f'    <text x="20" y="{y}" fill="#DDD6FE" font-family="\'Courier New\', monospace" '
                     f'font-size="12">{label}</text>')
        lines.append(f'    <text x="360" y="{y}" fill="#F0ABFC" font-family="\'Courier New\', monospace" '
                     f'font-size="12" font-weight="bold" text-anchor="end">{value}</text>')
    lines += [
        '    <rect x="20" y="235" width="340" height="12" fill="#2D2244" rx="3" />',
        '    <rect x="20" y="235" width="280" height="12" fill="#C084FC" rx="3" />',
        '    <rect x="20" y="235" width="70" height="12" fill="#FFFFFF" opacity="0" rx="3">',
        '      <animate attributeName="opacity" values="0;0.35;0.35;0" keyTimes="0;0.12;0.88;1" '
        'dur="2.8s" begin="0.6s" repeatCount="indefinite" />',
        '      <animateTransform attributeName="transform" type="translate" values="0 0;270 0;0 0" '
        'keyTimes="0;0.5;1" dur="2.8s" begin="0.6s" repeatCount="indefinite" />',
        '    </rect>',
        '  </g>',
    ]
    return "\n".join(lines)


def stats_row_svg(radar_part, stats_group_xml):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 850 360" width="100%" height="100%" '
        'shape-rendering="crispEdges" role="img" aria-label="Skill radar and GitHub stats">\n'
        '  <rect x="0" y="0" width="850" height="360" fill="#181124" />\n'
        + radar_part.strip()
        + "\n"
        + stats_group_xml
        + "\n</svg>\n"
    )


def main():
    args = sys.argv[1:]
    mock = "--mock" in args
    out_dir = os.path.abspath(args[args.index("--out") + 1]) if "--out" in args else ASSETS

    stats = MOCK_DATA if mock else collect()

    with open(os.path.join(ASSETS, "radar-part.svg"), encoding="utf-8") as handle:
        radar_part = handle.read()

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "top-languages-mac.svg"), "w", encoding="utf-8") as handle:
        handle.write(top_languages_svg(stats["lang_bytes"]))
    with open(os.path.join(out_dir, "stats-row.svg"), "w", encoding="utf-8") as handle:
        handle.write(stats_row_svg(radar_part, stats_group(stats)))

    if mock:
        print("[mock] generated cards from sample data")
    else:
        print("[live] generated cards from GitHub API")
    print("  stars=%s commits=%s prs=%s followers=%s langs=%s"
          % (stats["stars"], stats["commits"], stats["prs"], stats["followers"], len(stats["lang_bytes"])))


if __name__ == "__main__":
    main()
