"""Download and unpack the SST-2 dev split.

Deliberately dependency-free (stdlib only): the dataset download must not fail
because of a library version, and a 7 MB zip does not justify `datasets`.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://dl.fbaipublicfiles.com/glue/data/SST-2.zip"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="data")
    args = parser.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    dev = dest / "SST-2" / "dev.tsv"
    if dev.exists():
        print(f"data already present: {dev} ({sum(1 for _ in dev.open(encoding='utf-8')) - 1} rows)")
        return 0

    print(f"downloading {URL}")
    with urllib.request.urlopen(URL, timeout=120) as resp:
        payload = resp.read()
    print(f"downloaded {len(payload) / 1e6:.1f} MB")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        archive.extractall(dest)

    rows = sum(1 for _ in dev.open(encoding="utf-8")) - 1
    print(f"extracted {dev} ({rows} rows)")
    # Touch a manifest so a later run can prove what was used.
    (dest / "MANIFEST.txt").write_text(f"{URL}\nsize={len(payload)}\nrows={rows}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
