import json, urllib.request
from pathlib import Path

API = "https://api.github.com/repos/itzzace/ytkace/releases/latest"
req = urllib.request.Request(API, headers={"User-Agent": "source-updater"})
rel = json.load(urllib.request.urlopen(req))
ver, date = rel["tag_name"].lstrip("v"), rel["published_at"]
body = (rel.get("body") or "").strip()

VARIANTS = [
    {"name": "YTKACE", "id": "com.google.ios.youtube", "ios16": False, "minOS": "17.0",
     "icon": "https://cookieys.github.io/icons/ytkace.png"},
    {"name": "YTKACE (iOS 16)", "id": "com.google.ios.youtube.ios16", "ios16": True, "minOS": "16.0",
     "icon": "https://cookieys.github.io/icons/ytkace-ios16.png"},
]

path = Path("apps.json")
src = json.loads(path.read_text()) if path.exists() else {
    "name": "Cookieys Source", "identifier": "com.cookieys.source",
    "subtitle": "Auto-tracks itzzace/ytkace", "tintColor": "FF0000",
    "apps": [], "news": []}

for var in VARIANTS:
    assets = [a for a in rel["assets"]
              if a["name"].endswith(".ipa") and ("iOS16" in a["name"]) == var["ios16"]]
    if not assets:
        continue
    a = assets[0]
    yt = a["name"].rsplit("_", 1)[-1].removesuffix(".ipa")  # YouTube base version

    app = next((x for x in src["apps"] if x["bundleIdentifier"] == var["id"]), None)
    if app is None:
        app = {"bundleIdentifier": var["id"], "developerName": "itzzace",
               "localizedDescription": "YouTube enhanced with YTKACE. Auto-tracked from github.com/itzzace/ytkace.",
               "tintColor": "FF0000", "versions": []}
        src["apps"].append(app)

    # keep only this variant's history (cleans up the old mixed entry)
    app["versions"] = [v for v in app["versions"]
                       if ("iOS16" in v["downloadURL"]) == var["ios16"]]

    entry = {"version": ver, "date": date, "localizedDescription": body,
             "downloadURL": a["browser_download_url"], "size": a["size"],
             "minOSVersion": var["minOS"]}
    if entry["downloadURL"] not in {v["downloadURL"] for v in app["versions"]}:
        app["versions"] = ([entry] + app["versions"])[:20]

    app.update(name=var["name"], iconURL=var["icon"],
               subtitle=f"YouTube {yt} · iOS {'16' if var['ios16'] else '17'}+",
               version=ver, versionDate=date, versionDescription=body,
               downloadURL=a["browser_download_url"], size=a["size"],
               minOSVersion=var["minOS"])

path.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n")
print(f"Source at {ver}")
