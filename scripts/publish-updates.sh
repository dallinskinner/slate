#!/usr/bin/env bash
# Build slate-desktop + the signed repo, then publish repo/ to GitHub Pages
# (github.com/dallinskinner/slate-updates). Bump VERSION in packaging/repo.conf first.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/packaging/repo.conf"
if git -C "$ROOT/repo" ls-files --error-unmatch "pool/main/slate-desktop_${VERSION}_all.deb" >/dev/null 2>&1; then
  echo "slate-desktop $VERSION is already published. Bump VERSION in packaging/repo.conf."; exit 1
fi
"$ROOT/scripts/build-packages.sh"
cd "$ROOT/repo"
git add -A
git commit -q -m "slate-desktop $VERSION"
git push -q
echo "published $VERSION -> $REPO_URL (GitHub Pages takes about a minute)"
