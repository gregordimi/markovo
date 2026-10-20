#!/usr/bin/env python3
"""
Poly Haven Asset Downloader for Markovo 3D CAD.

Downloads PBR materials, HDRIs, and models directly from Poly Haven's public API
into the project's assets/ directory.

Usage:
    python3 scripts/download_polyhaven.py <asset_name_or_url> [--resolution 1k|2k|4k|8k] [--type blend|textures]

Examples:
    # Download 4K blend file & textures for brown floor tiles:
    python3 scripts/download_polyhaven.py brown_floor_tiles --resolution 4k

    # Download by URL:
    python3 scripts/download_polyhaven.py https://polyhaven.com/a/brown_floor_tiles
"""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import zipfile


API_BASE = "https://api.polyhaven.com/files"


def parse_asset_id(input_str: str) -> str:
    """Extracts the clean asset ID from a slug, name, or full Poly Haven URL."""
    input_str = input_str.strip().rstrip("/")
    if "polyhaven.com/a/" in input_str:
        return input_str.split("polyhaven.com/a/")[-1].split("?")[0].split("#")[0]
    return input_str


def fetch_asset_files_metadata(asset_id: str) -> dict:
    """Queries Poly Haven API for file availability and direct download links."""
    url = f"{API_BASE}/{asset_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Markovo-CAD-Asset-Downloader/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Poly Haven API returned HTTP {resp.status} for '{asset_id}'")
        return json.loads(resp.read().decode("utf-8"))


def download_file(url: str, dest_path: Path, label: str = ""):
    """Downloads a remote file with progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Markovo-CAD-Asset-Downloader/1.0"},
    )
    print(f"  -> Downloading {label or dest_path.name}...")
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
        total_len = resp.headers.get("Content-Length")
        total_bytes = int(total_len) if total_len else 0
        downloaded = 0
        chunk_size = 64 * 1024

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total_bytes > 0:
                percent = (downloaded / total_bytes) * 100
                sys.stdout.write(f"\r     [{percent:5.1f}%] {downloaded / (1024*1024):.1f} MB / {total_bytes / (1024*1024):.1f} MB")
                sys.stdout.flush()
        print()


def download_asset(
    asset_id: str,
    resolution: str = "4k",
    target_dir: Path = None,
    asset_type: str = "blend",
) -> Path:
    """Downloads an asset (blend package and/or textures) into assets/ directory."""
    if target_dir is None:
        target_dir = Path(__file__).resolve().parent.parent / "assets"

    asset_dir = target_dir / f"{asset_id}_{resolution}.blend"
    asset_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching metadata for '{asset_id}' (resolution: {resolution})...")
    meta = fetch_asset_files_metadata(asset_id)

    # 1. Download Blender .blend file if requested and available
    if asset_type in ("blend", "all") and "blend" in meta:
        blend_info = meta["blend"].get(resolution) or meta["blend"].get(list(meta["blend"].keys())[0])
        if blend_info and "blend" in blend_info:
            file_url = blend_info["blend"]["url"]
            blend_dest = asset_dir / f"{asset_id}_{resolution}.blend"
            download_file(file_url, blend_dest, label=f"Blender Scene ({blend_dest.name})")

    # 2. Download PBR Textures
    textures_dir = asset_dir / "textures"
    textures_dir.mkdir(parents=True, exist_ok=True)

    if asset_type in ("textures", "blend", "all"):
        # Poly Haven material texture channels
        # Typically under meta[channel][resolution][ext]
        for channel, formats in meta.items():
            if channel in ("blend", "gltf", "fbx", "usd"):
                continue
            if isinstance(formats, dict) and resolution in formats:
                res_dict = formats[resolution]
                # Prefer jpg or exr/png
                best_fmt = None
                for fmt in ("exr", "png", "jpg"):
                    if fmt in res_dict:
                        best_fmt = fmt
                        break
                if not best_fmt and res_dict:
                    best_fmt = list(res_dict.keys())[0]

                if best_fmt and "url" in res_dict[best_fmt]:
                    tex_url = res_dict[best_fmt]["url"]
                    ext = res_dict[best_fmt].get("extension", best_fmt)
                    tex_name = f"{asset_id}_{channel}_{resolution}.{ext}"
                    dest_file = textures_dir / tex_name
                    if not dest_file.exists():
                        download_file(tex_url, dest_file, label=f"Map: {channel} ({ext})")

    print(f"\nAsset '{asset_id}' successfully prepared in: {asset_dir}")
    return asset_dir


def main():
    parser = argparse.ArgumentParser(description="Download Poly Haven assets for Markovo 3D CAD.")
    parser.add_argument("asset", help="Asset slug or URL (e.g. brown_floor_tiles or https://polyhaven.com/a/...)")
    parser.add_argument("--resolution", "-r", default="4k", choices=["1k", "2k", "4k", "8k"], help="Texture resolution")
    parser.add_argument("--type", "-t", default="blend", choices=["blend", "textures", "all"], help="Asset bundle format")
    parser.add_argument("--output", "-o", default=None, help="Custom output directory")

    args = parser.parse_args()
    asset_id = parse_asset_id(args.asset)
    target_dir = Path(args.output).resolve() if args.output else None

    try:
        download_asset(asset_id, resolution=args.resolution, target_dir=target_dir, asset_type=args.type)
    except Exception as e:
        print(f"Error downloading asset: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
