#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
OUTPUT=${1:-_site}

if [[ -z "$OUTPUT" || "$OUTPUT" == "/" ]]; then
  echo "Refusing to use an unsafe output directory: '$OUTPUT'" >&2
  exit 2
fi

rm -rf -- "$OUTPUT"
mkdir -p -- "$OUTPUT"

python "$ROOT/create_repository.py" --datadir="$OUTPUT" \
  'https://github.com/choupacca/Kodi.git#master:' \
  'https://github.com/Soap4me/Kodi.git#py2:' \
  'https://github.com/eschava/soap4me-proxy.git:' \
  "$ROOT/repository.choupacca.soap4me"

# The existing generator creates checksums for Git sources, but not local folders.
# Recalculate all archive checksums so every published ZIP is covered uniformly.
python - "$OUTPUT" <<'PY'
import hashlib
import pathlib
import sys

site = pathlib.Path(sys.argv[1])
for archive in site.rglob("*.zip"):
    archive.with_suffix(archive.suffix + ".md5").write_text(
        hashlib.md5(archive.read_bytes()).hexdigest() + "\n",
        encoding="ascii",
    )
PY

cp "$ROOT/site/index.html" "$OUTPUT/index.html"
cp "$ROOT/site/.nojekyll" "$OUTPUT/.nojekyll"
