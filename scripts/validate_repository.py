#!/usr/bin/env python3
"""Validate the generated GitHub Pages Kodi repository."""

import hashlib
import pathlib
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile


EXPECTED = {
    "plugin.video.soap4.me": "1.3.0",
    "plugin.video.soap4-py2.me": None,
    "service.xbmc.soap4me": None,
    "repository.choupacca.soap4me": "1.0.1",
}
BASE_URL = "https://choupacca.github.io/Kodi-repo/"
INSTALLER = (
    "repository.choupacca.soap4me/"
    "repository.choupacca.soap4me-1.0.0.zip"
)


def digest(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def main(raw_site):
    site = pathlib.Path(raw_site)
    catalog_path = site / "addons.xml"
    catalog = ET.parse(catalog_path).getroot()

    assert (site / "addons.xml.md5").read_text(encoding="ascii").strip() == digest(catalog_path)
    for metadata in site.glob("*/addon.xml"):
        ET.parse(metadata)

    addons = {addon.get("id"): addon for addon in catalog.findall("addon")}
    assert set(addons) == set(EXPECTED), (set(addons), set(EXPECTED))
    for addon_id, version in EXPECTED.items():
        if version is not None:
            assert addons[addon_id].get("version") == version

    assert (site / "plugin.video.soap4.me/plugin.video.soap4.me-1.3.0.zip").is_file()
    assert (site / INSTALLER).is_file()

    for archive in site.glob("*/*.zip"):
        addon_id = archive.parent.name
        with zipfile.ZipFile(archive) as zipped:
            roots = {name.split("/", 1)[0] for name in zipped.namelist() if name}
        assert roots == {addon_id}, (archive, roots)
        checksum = archive.with_suffix(".zip.md5")
        assert checksum.is_file(), checksum
        assert checksum.read_text(encoding="ascii").strip() == digest(archive)

    repo = addons["repository.choupacca.soap4me"].find(
        "extension[@point='xbmc.addon.repository']"
    )
    assert repo is not None
    for element, expected in (
        ("info", "addons.xml"),
        ("checksum", "addons.xml.md5"),
        ("datadir", ""),
    ):
        node = repo.find(element)
        assert node is not None and node.text == BASE_URL + expected
        relative = urllib.parse.urlparse(node.text).path.removeprefix("/Kodi-repo/")
        assert (site / relative).exists()
    assert repo.find("datadir").get("zip") == "true"

    page = (site / "index.html").read_text(encoding="utf-8")
    assert f'href="{INSTALLER}"' in page
    assert (site / ".nojekyll").is_file()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "_site")
