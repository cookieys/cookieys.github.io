import requests
import json
from datetime import datetime

UPSTREAM = "itzzace/ytkace"
OUTPUT = "apps.json"
SOURCE_URL = "https://cookieys.github.io/apps.json"

def head_size(url: str) -> int:
    try:
        r = requests.head(url, allow_redirects=True, timeout=15)
        return int(r.headers.get("content-length", 0))
    except Exception:
        return 0

def main():
    r = requests.get(
        f"https://api.github.com/repos/{UPSTREAM}/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()

    tag = data["tag_name"]
    version = tag.lstrip("v")
    release_date = data["published_at"][:10]

    ios17 = None
    ios16 = None
    for a in data["assets"]:
        name = a["name"]
        if not name.lower().endswith(".ipa"):
            continue
        if "iOS16" in name:
            ios16 = a
        elif "YouTube" in name:
            ios17 = a

    apps = []

    if ios17:
        apps.append({
            "name": "YTKACE (iOS 17+)",
            "bundleIdentifier": "com.google.ios.youtube",
            "developerName": "itzzace",
            "subtitle": "YouTube enhancer for iOS 17+",
            "localizedDescription": (
                f"YTKACE {version} for iOS 17+. "
                "Auto-updated from the latest itzzace/ytkace release."
            ),
            "iconURL": "https://raw.githubusercontent.com/itzzace/ytkace/main/icon.png",
            "tintColor": "#FF0000",
            "category": "utilities",
            "versions": [{
                "version": version,
                "date": release_date,
                "downloadURL": ios17["browser_download_url"],
                "size": ios17.get("size") or head_size(ios17["browser_download_url"]),
                "minOSVersion": "17.0",
            }],
        })

    if ios16:
        apps.append({
            "name": "YTKACE (iOS 16)",
            "bundleIdentifier": "com.google.ios.youtube.ios16",
            "developerName": "itzzace",
            "subtitle": "YouTube enhancer for iOS 16",
            "localizedDescription": (
                f"YTKACE {version} for iOS 16. "
                "Auto-updated from the latest itzzace/ytkace release."
            ),
            "iconURL": "https://raw.githubusercontent.com/itzzace/ytkace/main/icon.png",
            "tintColor": "#FF0000",
            "category": "utilities",
            "versions": [{
                "version": version,
                "date": release_date,
                "downloadURL": ios16["browser_download_url"],
                "size": ios16.get("size") or head_size(ios16["browser_download_url"]),
                "minOSVersion": "16.0",
            }],
        })

    repo = {
        "name": "Cookiey's Repo",
        "identifier": "io.github.cookieys.repo",
        "sourceURL": SOURCE_URL,
        "subtitle": "Auto-tracking YTKACE releases",
        "description": "Mirrors the latest itzzace/ytkace release as a sideloadable source.",
        "iconURL": "https://raw.githubusercontent.com/itzzace/ytkace/main/icon.png",
        "headerURL": "",
        "website": "https://github.com/itzzace/ytkace",
        "tintColor": "#FF0000",
        "featuredApps": [],
        "apps": apps,
        "news": [],
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote {OUTPUT} — version {version}, {len(apps)} app(s)")

if __name__ == "__main__":
    main()
