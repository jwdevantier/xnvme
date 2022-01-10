#!/usr/bin/env python3
"""
    Injects 'subproject/packagefiles' into a 'meson dist' zip-archive

    When running 'meson dist', then the test-stage will fail as 'meson.build'
    and other files from the packagefiles are not available in the subproject's
    folder. This is not the same behavior as when building normally. However,
    it seems to be intended behavior:

    https://github.com/mesonbuild/meson/issues/8127

    Thus to work around that, this script injects the subprojects/packagefiles
    into a zip-archive generated by 'meson dist, like:

    meson dist --include-subprojects --no-tests --formats zip

    The zip-format is required as it seems like the simplest way to edit
    archives, tarfile with compression might work, but did not attempt it. The
    implementation defensively skips if the 'arcname' already exists, that is,
    the name path within the archive.
"""
import argparse
import zipfile
import os
import sys
from pathlib import Path


def expand_path(path):
    """Expands variables from the given path and turns it into absolute path"""

    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def parse_args():
    """Parse arguments for dist-archive-fixer"""

    prsr = argparse.ArgumentParser(
        description="Meson dist-archive fixer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    prsr.add_argument(
        "--archive",
        required=True,
        help="Path to 'meson dist' generated zip-file",
    )
    prsr.add_argument(
        "--files",
        required=True,
        help="Path meson 'subprojects/packagefiles'",
    )

    return prsr.parse_args()


def main(args):
    """Main entry point"""

    args.archive = expand_path(args.archive)
    args.files = expand_path(args.files)

    def additions(search_path):
        """Generate a list of (lpath, arcname) for writing to zip-file"""

        aname = Path(args.archive).stem
        for root, _, files in os.walk(search_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = fpath.replace(
                    search_path,
                    "/".join([aname, 'subprojects'])
                )
                yield fpath, arcname

    with zipfile.ZipFile(args.archive, 'a') as zfile:
        listing = zfile.namelist()
        for lpath, arcname in additions(args.files):
            if arcname in listing:
                print(f"skipping: {lpath} {arcname}")
                continue
            zfile.write(lpath, arcname)

    return 0

if __name__ == "__main__":
    sys.exit(main(parse_args()))
