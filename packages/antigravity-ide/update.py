#!/usr/bin/env nix
#! nix shell --inputs-from .# nixpkgs#python3 --command python3

"""Update script for Antigravity IDE."""

import re
import sys
from pathlib import Path
from typing import Any, cast

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from updater import (
    fetch_json,
    load_hashes,
    save_hashes,
    should_update,
)
from updater.hash import hex_to_sri

HASHES_FILE = Path(__file__).parent / "hashes.json"
UPDATE_API = (
    "https://antigravity-ide-auto-updater-974169037036.us-central1.run.app"
    "/api/update/{target_system}/stable/latest"
)
PLATFORMS = {
    "x86_64-linux": "linux-x64",
    "aarch64-linux": "linux-arm64",
    "aarch64-darwin": "darwin-arm64",
}


def fetch_platform_info(target_system: str) -> dict[str, str]:
    """Fetch the latest update info for a platform."""
    result = fetch_json(UPDATE_API.format(target_system=target_system))
    info = cast("dict[str, Any]", result)
    # Version is embedded in the URL; extract it.
    url = str(info["url"])
    match = re.search(r"/antigravity/stable/([\d.]+)-\d+", url)
    if match is None:
        msg = f"Could not parse Antigravity IDE version from {url}"
        raise RuntimeError(msg)
    return {
        "version": match.group(1),
        "vscodeVersion": str(info["productVersion"]),
        "url": url.replace(" ", "%20"),
        "sha256hex": str(info["sha256hash"]),
    }


def main() -> None:
    """Update the Antigravity IDE package."""
    data = load_hashes(HASHES_FILE)
    current = str(data["version"])

    first_info = fetch_platform_info(PLATFORMS["x86_64-linux"])
    latest = first_info["version"]
    vscode_version = first_info["vscodeVersion"]

    print(f"Current: {current}, Latest: {latest}")

    if not should_update(current, latest):
        print("Already up to date")
        return

    sources: dict[str, dict[str, str]] = {}
    platform_infos: dict[str, dict[str, str]] = {"x86_64-linux": first_info}

    for nix_platform, target_system in PLATFORMS.items():
        info = platform_infos.get(nix_platform) or fetch_platform_info(target_system)
        if info["version"] != latest:
            msg = f"{nix_platform} has version {info['version']}, expected {latest}"
            raise RuntimeError(msg)

        sources[nix_platform] = {
            "url": info["url"],
            "sha256": hex_to_sri(info["sha256hex"], "sha256"),
        }
        print(f"  {nix_platform}: {sources[nix_platform]['sha256']}")

    save_hashes(
        HASHES_FILE,
        {
            "version": latest,
            "vscodeVersion": vscode_version,
            "sources": sources,
        },
    )

    print(f"Updated to {latest}")


if __name__ == "__main__":
    main()
