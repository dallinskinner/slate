#!/usr/bin/env bash
# Publish website/ to GitHub Pages (gh-pages branch of github.com/dallinskinner/slate).
# Commit your website changes on main first.
set -euo pipefail
cd "$(dirname "$0")/.."
git subtree split -q --prefix website -b gh-pages
git push -q -f origin gh-pages
echo "published -> https://dallinskinner.github.io/slate (about a minute)"
