# Cookiey's Repo 🍪

[![Tests](https://github.com/cookieys/cookieys.github.io/actions/workflows/tests.yml/badge.svg)](https://github.com/cookieys/cookieys.github.io/actions/workflows/tests.yml)
[![Update](https://github.com/cookieys/cookieys.github.io/actions/workflows/update.yml/badge.svg)](https://github.com/cookieys/cookieys.github.io/actions/workflows/update.yml)

An iOS sideloading source that automatically tracks the latest
[YTKACE](https://github.com/itzzace/ytkace) release.

**Source URL:** `https://cookieys.github.io/apps.json`

## Install

1. Install [AltStore](https://altstore.io), [SideStore](https://sidestore.io) or
   [Feather](https://github.com/khcrysalis/Feather).
2. Open <https://cookieys.github.io> and tap **Add to …**, or paste the source URL
   above into your app's *Add Source* field.
3. Install the build that matches your iOS version (**iOS 16** or **iOS 17+**).

## How it works

- A GitHub Action runs every 6 hours (and on demand) and executes `update_repo.py`.
- The script reads the latest `itzzace/ytkace` release, builds the source JSON and
  **validates it before writing**. If upstream changes in a way that breaks the
  expected format, the run fails and the existing `apps.json` is left untouched.
- The last 5 versions of each app are kept, so older builds stay available.
- This repo stores metadata and links only. The IPAs are hosted upstream.

## Development

```bash
pip install -r requirements.txt
python -m unittest discover -v   # run the tests (no network needed)
python update_repo.py --validate # validate the committed apps.json
python update_repo.py            # fetch the latest release and rewrite apps.json
```

Set `GITHUB_TOKEN` in your environment to avoid GitHub API rate limits when
running locally.

## Disclaimer

Not affiliated with itzzace or Google. Use at your own risk.
