#!/usr/bin/env python3
"""Headless / batch SDL publisher driven by a YAML manifest.

Usage:
    # 1) generate an annotated manifest skeleton from a project folder:
    python sdl_publish_manifest.py generate <project_dir> [out.yml]

    # 2) fill in the TODO fields, then publish (non-interactive):
    SDL_USERNAME=you@example.org SDL_PASSWORD=... \
        python sdl_publish_manifest.py publish <manifest.yml>

If SDL_USERNAME / SDL_PASSWORD are not set, you are prompted (password hidden).
Requires sdl_lib.py in the same folder. Needs: requests requests_toolbelt rasterio
cmocean matplotlib numpy tqdm pyyaml jsonschema (all present in the HySEALab `lab_gpu` env).
"""
import os
import sys
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sdl_lib


USAGE = (
    "usage:\n"
    "  python sdl_publish_manifest.py generate <project_dir> [out.yml]\n"
    "  python sdl_publish_manifest.py publish  <manifest.yml>\n"
)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("generate", "publish"):
        print(USAGE)
        return 2

    if argv[0] == "generate":
        out = argv[2] if len(argv) > 2 else None
        sdl_lib.generate_manifest(argv[1], out)
        return 0

    # publish
    manifest = argv[1]
    user = os.environ.get("SDL_USERNAME") or input("SDL username (email): ").strip()
    pw = os.environ.get("SDL_PASSWORD") or getpass.getpass("SDL password: ")
    try:
        result = sdl_lib.publish_from_manifest(manifest, user, pw)
    except Exception as e:
        print(f"\n❌ Publish failed: {type(e).__name__}: {e}")
        return 1
    print(f"\n✅ {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
