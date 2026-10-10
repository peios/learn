#!/usr/bin/env bash
# Static preview build only; hosting and Git integration are configured separately.
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
out=${1:-"$repo/dist"}
if [[ $# -gt 1 ]]; then
  echo 'Usage: build_cloudflare_preview.sh [output-directory]' >&2
  exit 2
fi
# Trail replaces its output directory. Never let that erase this checkout.
out=$(python3 - "$repo" "$out" <<'PYOUT'
from pathlib import Path
import sys
repo, out = (Path(p).resolve() for p in sys.argv[1:])
if out == repo or out in repo.parents or (repo in out.parents and out != repo / 'dist'):
    raise SystemExit('Output must be repo/dist or a separate directory, not site sources or an ancestor')
print(out)
PYOUT
)
# Fail closed if accidentally used for this repository's production branch.
if [[ ${CF_PAGES_BRANCH:-} == main ]]; then
  echo 'Cloudflare previews must not build the main production branch.' >&2
  exit 1
fi
: "${CF_PAGES_URL:?Set CF_PAGES_URL to the HTTPS preview deployment origin}"

work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
mkdir "$work/site"
# Trail accepts only its config and products at the site root, plus passthroughs.
cp -- "$repo/trail.toml" "$repo/CNAME" "$work/site/"
cp -R -- "$repo"/*.product "$repo/.well-known" "$work/site/"
# Trail has no environment-specific config or --base-url flag. Change only a
# disposable copy, so production config and all authored content stay untouched.
python3 - "$work/site/trail.toml" <<'PY'
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

url = os.environ['CF_PAGES_URL'].rstrip('/')
parts = urlsplit(url)
if (parts.scheme != 'https' or not parts.hostname
        or not parts.hostname.endswith('.pages.dev') or parts.username
        or parts.password or parts.port or parts.path or parts.query or parts.fragment):
    raise SystemExit('CF_PAGES_URL must be an HTTPS *.pages.dev origin without a path')
path = Path(sys.argv[1])
text = path.read_text()
# Stop before TOML tables; nav entries also contain keys named url.
root, marker, tables = text.partition('[[nav]]')
root, count = re.subn(r'^url\s*=.*$', 'url = ' + json.dumps(url), root, flags=re.MULTILINE)
if count != 1:
    raise SystemExit('Expected exactly one root url in trail.toml')
path.write_text(root + marker + tables)
PY

# Same reviewed artifact as the read-only pull-request validation workflow.
# The upstream latest tag is mutable: a replacement must fail until reviewed.
trail_sha256=a84799039de3088177fddeee213f27a072f71c84070a9ccd957263abb7a7c5a1
if [[ -n ${TRAIL_BIN:-} ]]; then
  cp -- "$TRAIL_BIN" "$work/trail"
else
  curl --fail --location --proto '=https' --proto-redir '=https' \
    --retry 3 --max-time 120 \
    https://github.com/peios/trail/releases/download/latest/trail-linux-amd64 \
    -o "$work/trail"
fi
printf '%s  %s\n' "$trail_sha256" "$work/trail" | sha256sum --check --status
chmod +x "$work/trail"
"$work/trail" --version
"$work/trail" build "$work/site" --strict --out "$out"
# CNAME belongs to GitHub Pages production only, not the preview artifact.
rm -- "$out/CNAME"
