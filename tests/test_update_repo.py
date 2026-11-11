import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import update_repo as u  # noqa: E402

IPA17 = "YTKACE_1.2.0_YouTube_21.45.4.ipa"
IPA16 = "YTKACE_1.2.0_YouTube_iOS16_21.33.6.ipa"


def asset(name, size=1000):
    return {
        "name": name,
        "size": size,
        "browser_download_url": f"https://github.com/itzzace/ytkace/releases/download/v1.2.0/{name}",
    }


def release(tag="v1.2.0", date="2026-12-01T10:00:00Z", assets=None):
    if assets is None:
        assets = [asset(IPA17, 1000), asset(IPA16, 2000)]
    return {"tag_name": tag, "published_at": date, "assets": assets}


def no_network(_url):
    raise AssertionError("size_lookup should not have been called")


class PickAssetTests(unittest.TestCase):
    def test_ios16_and_ios17_are_distinguished(self):
        assets = [asset(IPA16), asset(IPA17)]
        a17 = u.pick_asset(assets, u.TARGETS[0]["match"])
        a16 = u.pick_asset(assets, u.TARGETS[1]["match"])
        self.assertEqual(a17["name"], IPA17)
        self.assertEqual(a16["name"], IPA16)

    def test_non_ipa_files_are_ignored(self):
        assets = [asset("YTKACE_YouTube.zip"), asset("notes.txt")]
        self.assertIsNone(u.pick_asset(assets, u.TARGETS[0]["match"]))

    def test_extension_is_case_insensitive(self):
        assets = [asset("YTKACE_1.0_YouTube_1.IPA")]
        self.assertIsNotNone(u.pick_asset(assets, u.TARGETS[0]["match"]))


class MergeVersionsTests(unittest.TestCase):
    def v(self, n):
        return {"version": n}

    def test_new_version_goes_first(self):
        out = u.merge_versions([self.v("1.0")], self.v("1.1"))
        self.assertEqual([x["version"] for x in out], ["1.1", "1.0"])

    def test_same_version_is_replaced_not_duplicated(self):
        out = u.merge_versions([self.v("1.1"), self.v("1.0")], {"version": "1.1", "size": 5})
        self.assertEqual([x["version"] for x in out], ["1.1", "1.0"])
        self.assertEqual(out[0]["size"], 5)

    def test_history_is_capped(self):
        old = [self.v(f"1.{i}") for i in range(10)]
        out = u.merge_versions(old, self.v("2.0"), limit=3)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[0]["version"], "2.0")


class BuildSourceTests(unittest.TestCase):
    def test_builds_both_apps(self):
        src = u.build_source(release(), None, no_network)
        names = [a["name"] for a in src["apps"]]
        self.assertEqual(names, ["YTKACE (iOS 17+)", "YTKACE (iOS 16)"])
        v = src["apps"][0]["versions"][0]
        self.assertEqual(v["version"], "1.2.0")
        self.assertEqual(v["date"], "2026-12-01")
        self.assertEqual(v["size"], 1000)
        self.assertEqual(v["minOSVersion"], "17.0")
        self.assertEqual(u.validate_source(src), [])

    def test_empty_release_raises_instead_of_wiping_source(self):
        with self.assertRaises(ValueError):
            u.build_source(release(assets=[]), None, no_network)

    def test_release_with_only_unrelated_assets_raises(self):
        with self.assertRaises(ValueError):
            u.build_source(release(assets=[asset("source.zip")]), None, no_network)

    def test_total_asset_mismatch_fails_even_with_history(self):
        # Upstream renamed everything: must fail loudly, not silently re-publish old data.
        first = u.build_source(release(), None, no_network)
        renamed = release(tag="v2.0.0", assets=[asset("totally_new_name.ipa")])
        with self.assertRaises(ValueError):
            u.build_source(renamed, first, no_network)

    def test_missing_ios16_asset_keeps_previous_entry(self):
        first = u.build_source(release(), None, no_network)
        newer = release(tag="v1.3.0", assets=[asset("YTKACE_1.3.0_YouTube_21.50.ipa", 3000)])
        out = u.build_source(newer, first, no_network)
        by_id = {a["bundleIdentifier"]: a for a in out["apps"]}
        self.assertEqual(by_id["com.google.ios.youtube"]["versions"][0]["version"], "1.3.0")
        # iOS 16 app survives with its old version rather than disappearing
        self.assertEqual(by_id["com.google.ios.youtube.ios16"]["versions"][0]["version"], "1.2.0")

    def test_missing_ios16_asset_with_no_history_is_just_skipped(self):
        rel = release(assets=[asset(IPA17)])
        out = u.build_source(rel, None, no_network)
        self.assertEqual(len(out["apps"]), 1)

    def test_zero_size_falls_back_to_lookup(self):
        rel = release(assets=[asset(IPA17, size=0)])
        out = u.build_source(rel, None, lambda url: 12345)
        self.assertEqual(out["apps"][0]["versions"][0]["size"], 12345)

    def test_zero_size_and_failed_lookup_fails_validation(self):
        rel = release(assets=[asset(IPA17, size=0)])
        out = u.build_source(rel, None, lambda url: 0)
        self.assertTrue(any("size" in e for e in u.validate_source(out)))

    def test_history_accumulates_across_releases(self):
        first = u.build_source(release(), None, no_network)
        second = u.build_source(
            release(
                tag="v1.3.0",
                date="2026-12-15T00:00:00Z",
                assets=[asset("YTKACE_1.3.0_YouTube_1.ipa"), asset("YTKACE_1.3.0_YouTube_iOS16_1.ipa")],
            ),
            first,
            no_network,
        )
        versions = [v["version"] for v in second["apps"][0]["versions"]]
        self.assertEqual(versions, ["1.3.0", "1.2.0"])

    def test_rerunning_same_release_is_idempotent(self):
        first = u.build_source(release(), None, no_network)
        again = u.build_source(release(), copy.deepcopy(first), no_network)
        self.assertEqual(first, again)

    def test_no_empty_header_url(self):
        src = u.build_source(release(), None, no_network)
        self.assertNotIn("headerURL", src)


class ValidateSourceTests(unittest.TestCase):
    def good(self):
        return u.build_source(release(), None, no_network)

    def test_good_source_has_no_errors(self):
        self.assertEqual(u.validate_source(self.good()), [])

    def test_empty_apps_is_invalid(self):
        s = self.good()
        s["apps"] = []
        self.assertTrue(u.validate_source(s))

    def test_missing_top_level_key(self):
        s = self.good()
        del s["identifier"]
        self.assertTrue(any("identifier" in e for e in u.validate_source(s)))

    def test_empty_url_is_flagged(self):
        s = self.good()
        s["headerURL"] = ""
        self.assertTrue(any("headerURL" in e for e in u.validate_source(s)))

    def test_http_download_url_is_flagged(self):
        s = self.good()
        s["apps"][0]["versions"][0]["downloadURL"] = "http://example.com/a.ipa"
        self.assertTrue(any("downloadURL" in e for e in u.validate_source(s)))

    def test_bad_date_is_flagged(self):
        s = self.good()
        s["apps"][0]["versions"][0]["date"] = "12/01/2026"
        self.assertTrue(any("date" in e for e in u.validate_source(s)))

    def test_duplicate_bundle_ids_are_flagged(self):
        s = self.good()
        s["apps"][1]["bundleIdentifier"] = s["apps"][0]["bundleIdentifier"]
        self.assertTrue(any("duplicate" in e for e in u.validate_source(s)))

    def test_missing_version_field_is_flagged(self):
        s = self.good()
        del s["apps"][0]["versions"][0]["minOSVersion"]
        self.assertTrue(any("minOSVersion" in e for e in u.validate_source(s)))


class CommittedFileTests(unittest.TestCase):
    """Guards the apps.json that is actually committed to the repo."""

    def test_committed_apps_json_is_valid(self):
        data = json.loads((ROOT / "apps.json").read_text(encoding="utf-8"))
        self.assertEqual(u.validate_source(data), [])


if __name__ == "__main__":
    unittest.main()
