"""Regenerate apps.json (an AltStore/SideStore/Feather source) from the
latest itzzace/ytkace GitHub release.

Usage:
    python update_repo.py              # fetch latest release, rewrite apps.json
    python update_repo.py --validate   # only validate the existing apps.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Callable

import requests

UPSTREAM = "itzzace/ytkace"
OUTPUT = Path("apps.json")
SOURCE_URL = "https://cookieys.github.io/apps.json"
ICON_URL = "https://raw.githubusercontent.com/itzzace/ytkace/main/icon.png"
MAX_VERSIONS = 5  # how many versions to keep per app (enables rollbacks)

# One entry per app we publish. `match` decides which release asset belongs to it.
TARGETS = [
    {
        "name": "YTKACE (iOS 17+)",
        "bundleIdentifier": "com.google.ios.youtube",
        "subtitle": "YouTube enhancer for iOS 17+",
        "ios_label": "iOS 17+",
        "minOSVersion": "17.0",
        "match": lambda n: "iOS16" not in n and "YouTube" in n,
    },
    {
        "name": "YTKACE (iOS 16)",
        "bundleIdentifier": "com.google.ios.youtube.ios16",
        "subtitle": "YouTube enhancer for iOS 16",
        "ios_label": "iOS 16",
        "minOSVersion": "16.0",
        "match": lambda n: "iOS16" in n,
    },
]

SizeLookup = Callable[[str], int]


# --------------------------------------------------------------------------
# Network helpers
# --------------------------------------------------------------------------
def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "cookieys-repo-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_latest_release(upstream: str = UPSTREAM) -> dict:
    r = requests.get(
        f"https://api.github.com/repos/{upstream}/releases/latest",
        headers=_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def head_size(url: str) -> int:
    """Fallback when the API doesn't report an asset size."""
    try:
        r = requests.head(url, allow_redirects=True, timeout=15)
        return int(r.headers.get("content-length", 0))
    except Exception:
        return 0


# --------------------------------------------------------------------------
# Pure logic (no network, easy to test)
# --------------------------------------------------------------------------
def pick_asset(assets: list[dict], match: Callable[[str], bool]) -> dict | None:
    for a in assets:
        name = a.get("name", "")
        if name.lower().endswith(".ipa") and match(name):
            return a
    return None


def merge_versions(existing: list[dict], new: dict, limit: int = MAX_VERSIONS) -> list[dict]:
    """Newest first; replaces an existing entry with the same version string."""
    rest = [v for v in existing if v.get("version") != new["version"]]
    return ([new] + rest)[:limit]


def _app_entry(target: dict, version: str, versions: list[dict]) -> dict:
    return {
        "name": target["name"],
        "bundleIdentifier": target["bundleIdentifier"],
        "developerName": "itzzace",
        "subtitle": target["subtitle"],
        "localizedDescription": (
            f"YTKACE {version} for {target['ios_label']}. "
            "Auto-updated from the latest itzzace/ytkace release."
        ),
        "iconURL": ICON_URL,
        "tintColor": "#FF0000",
        "category": "utilities",
        "versions": versions,
    }


def build_source(
    release: dict,
    existing: dict | None = None,
    size_lookup: SizeLookup = head_size,
) -> dict:
    """Build the full source dict. Raises ValueError if nothing usable is found."""
    version = release["tag_name"].lstrip("v")
    release_date = release["published_at"][:10]
    assets = release.get("assets", [])
    old_apps = {a.get("bundleIdentifier"): a for a in (existing or {}).get("apps", [])}

    apps = []
    matched = 0  # assets found in THIS release (carried-over entries don't count)
    for t in TARGETS:
        asset = pick_asset(assets, t["match"])
        old = old_apps.get(t["bundleIdentifier"])
        if asset is None:
            if old:  # don't silently drop an app because upstream renamed a file
                print(f"⚠️  No asset for {t['name']} in {version}; keeping previous entry")
                apps.append(old)
            continue
        matched += 1
        url = asset["browser_download_url"]
        entry = {
            "version": version,
            "date": release_date,
            "downloadURL": url,
            "size": asset.get("size") or size_lookup(url),
            "minOSVersion": t["minOSVersion"],
        }
        versions = merge_versions((old or {}).get("versions", []), entry)
        apps.append(_app_entry(t, version, versions))

    if not matched:
        raise ValueError(
            "No matching .ipa assets found in the latest release; "
            "refusing to publish a stale or empty source."
        )

    return {
        "name": "Cookiey's Repo",
        "identifier": "io.github.cookieys.repo",
        "sourceURL": SOURCE_URL,
        "subtitle": "Auto-tracking YTKACE releases",
        "description": "Mirrors the latest itzzace/ytkace release as a sideloadable source.",
        "iconURL": ICON_URL,
        "website": f"https://github.com/{UPSTREAM}",
        "tintColor": "#FF0000",
        "featuredApps": [],
        "apps": apps,
        "news": [],
    }


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _check_urls(node, path: str, errors: list[str]) -> None:
    """Flag empty or non-https values in any key ending in 'URL'."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k.endswith("URL"):
                if not isinstance(v, str) or not v.startswith("https://"):
                    errors.append(f"{path}.{k} must be an https URL (got {v!r})")
            else:
                _check_urls(v, f"{path}.{k}", errors)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _check_urls(item, f"{path}[{i}]", errors)


def validate_source(src: dict) -> list[str]:
    """Return a list of problems (empty list means valid)."""
    errors: list[str] = []
    for key in ("name", "identifier", "sourceURL", "apps"):
        if key not in src:
            errors.append(f"missing top-level key: {key}")
    apps = src.get("apps")
    if not isinstance(apps, list) or not apps:
        errors.append("'apps' must be a non-empty list")
        return errors

    _check_urls(src, "source", errors)

    seen_ids = set()
    for i, app in enumerate(apps):
        where = f"apps[{i}]"
        for key in ("name", "bundleIdentifier", "developerName", "versions"):
            if not app.get(key):
                errors.append(f"{where}: missing '{key}'")
        bid = app.get("bundleIdentifier")
        if bid in seen_ids:
            errors.append(f"{where}: duplicate bundleIdentifier {bid}")
        seen_ids.add(bid)

        for j, v in enumerate(app.get("versions") or []):
            vw = f"{where}.versions[{j}]"
            for key in ("version", "date", "downloadURL", "size", "minOSVersion"):
                if key not in v:
                    errors.append(f"{vw}: missing '{key}'")
            if "date" in v and not _DATE_RE.match(str(v["date"])):
                errors.append(f"{vw}: date must be YYYY-MM-DD (got {v['date']!r})")
            size = v.get("size")
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                errors.append(f"{vw}: size must be a positive integer (got {size!r})")
    return errors


# --------------------------------------------------------------------------
# I/O + CLI
# --------------------------------------------------------------------------
def load_existing(path: Path = OUTPUT) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_source(src: dict, path: Path = OUTPUT) -> None:
    path.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--validate" in argv:
        existing = load_existing()
        if existing is None:
            print(f"❌ {OUTPUT} is missing or not valid JSON")
            return 1
        errors = validate_source(existing)
        for e in errors:
            print(f"❌ {e}")
        if not errors:
            print(f"✅ {OUTPUT} is valid")
        return 1 if errors else 0

    try:
        src = build_source(fetch_latest_release(), load_existing())
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    errors = validate_source(src)
    if errors:
        for e in errors:
            print(f"❌ {e}")
        print(f"Refusing to overwrite {OUTPUT}")
        return 1

    write_source(src)
    latest = src["apps"][0]["versions"][0]["version"]
    print(f"✅ Wrote {OUTPUT} — version {latest}, {len(src['apps'])} app(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
