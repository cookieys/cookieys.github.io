import json, urllib.request
from pathlib import Path

API = "https://api.github.com/repos/itzzace/ytkace/releases/latest"
req = urllib.request.Request(API, headers={"User-Agent": "source-updater"})
rel = json.load(urllib.request.urlopen(req))

ver, date = rel["tag_name"].lstrip("v"), rel["published_at"]
body = (rel.get("body") or "").strip()
ipas = [a for a in rel["assets"] if a["name"].endswith(".ipa")]

def entry(a):
    v = {"version": ver, "date": date, "localizedDescription": body,
         "downloadURL": a["browser_download_url"], "size": a["size"],
         "minOSVersion": "17.0"}
    if "iOS16" in a["name"]:
        v.update(minOSVersion="16.0", maxOSVersion="16.99")
    return v

new = [entry(a) for a in ipas]
primary = next((v for v in new if "maxOSVersion" not in v), new[0])

path = Path("apps.json")
src = json.loads(path.read_text()) if path.exists() else {
    "name": "Cookieys Source", "identifier": "com.cookieys.source",
    "subtitle": "Auto-tracks itzzace/ytkace", "tintColor": "FF0000",
    "apps": [], "news": []}

app = next((a for a in src["apps"] if a["bundleIdentifier"] == "com.google.ios.youtube"), None)
if app is None:
    app = {"name": "YTKACE", "bundleIdentifier": "com.google.ios.youtube",
           "developerName": "itzzace", "subtitle": "YouTube with downloads, SponsorBlock & more",
           "localizedDescription": "YouTube enhanced with YTKACE. Auto-tracked from github.com/itzzace/ytkace.",
           "iconURL": "https://github.com/itzzace.png", "tintColor": "FF0000", "versions": []}
    src["apps"].append(app)

known = {v["downloadURL"] for v in app["versions"]}
if any(v["downloadURL"] not in known for v in new):
    app["versions"] = (new + app["versions"])[:20]
    app.update(version=ver, versionDate=date, versionDescription=body,
               downloadURL=primary["downloadURL"], size=primary["size"])
    path.write_text(json.dumps(src, indent=2, ensure_ascii=False) + "\n")
    print(f"Updated to {ver}")
else:
    print("Already up to date")
