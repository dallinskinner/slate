#!/usr/bin/env bash
# Build the slate-desktop .deb (everything in overlay/ + the Slate update-server source)
# and add it to the signed apt repository in repo/. Upload repo/ to REPO_URL to publish.
#   ./scripts/build-packages.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/packaging/repo.conf"
# Test builds: TEST_REPO_URL=http://10.0.2.2:8000 TEST_REPO_DIR=/some/dir ./scripts/build-packages.sh
REPO_URL="${TEST_REPO_URL:-$REPO_URL}"
VERSION="${TEST_VERSION:-$VERSION}"
PKG="$ROOT/packaging/slate-desktop"
STAGE="$ROOT/build/pkg-stage/slate-desktop"
REPO="${TEST_REPO_DIR:-$ROOT/repo}"
export GNUPGHOME="$ROOT/packaging/gnupg"   # PRIVATE signing key: back it up, never upload it

# 1. Signing key (created once). Losing it means existing installs can't verify updates.
mkdir -p "$GNUPGHOME"; chmod 700 "$GNUPGHOME"
if ! gpg --list-secret-keys --with-colons 2>/dev/null | grep -q '^sec'; then
  echo "Creating the Slate archive signing key in packaging/gnupg/ (back this folder up!)"
  gpg --batch --passphrase '' --quick-gen-key "Slate Archive Signing Key" ed25519 sign never
fi
KEYID=$(gpg --list-secret-keys --with-colons | awk -F: '/^fpr/{print $10; exit}')

# 2. Package tree
rm -rf "$STAGE"; mkdir -p "$STAGE/DEBIAN"
cp -a "$ROOT/overlay/." "$STAGE/"
install -Dm644 "$ROOT/branding/slate-logo.svg" "$STAGE/usr/share/slate/slate-logo.svg"
install -d "$STAGE/usr/share/keyrings" "$STAGE/etc/apt/sources.list.d"
gpg --export "$KEYID" > "$STAGE/usr/share/keyrings/slate-archive-keyring.gpg"
cat > "$STAGE/etc/apt/sources.list.d/slate.sources" <<SRC
# Slate updates (theme, wallpapers, branding, new Slate versions)
Types: deb
URIs: $REPO_URL/
Suites: $SUITE
Components: main
Signed-By: /usr/share/keyrings/slate-archive-keyring.gpg
SRC
chmod -R u+rwX,go+rX,go-w "$STAGE"   # no group-writable files from the checkout
for s in preinst postinst postrm; do install -m755 "$PKG/$s" "$STAGE/DEBIAN/$s"; done
install -m644 "$PKG/triggers" "$STAGE/DEBIAN/triggers"
(cd "$STAGE" && find etc -type f | sort | sed 's|^|/|') > "$STAGE/DEBIAN/conffiles"
SIZE=$(du -sk --exclude=DEBIAN "$STAGE" | cut -f1)
sed -e "s/@VERSION@/$VERSION/" -e "s/@SIZE@/$SIZE/" "$PKG/control.in" > "$STAGE/DEBIAN/control"
PKGOUT="${TEST_REPO_DIR:+$TEST_REPO_DIR.debs}"; PKGOUT="${PKGOUT:-$ROOT/build/packages}"
mkdir -p "$PKGOUT"
DEB="$PKGOUT/slate-desktop_${VERSION}_all.deb"
dpkg-deb --root-owner-group -Zxz --build "$STAGE" "$DEB" >/dev/null
echo "built $DEB"
DEBS=("$DEB")

# 2b. slate-facetimehd: optional Mac camera driver (DKMS) + firmware downloader
F="$ROOT/packaging/slate-facetimehd"
. "$F/version.conf"     # sets VERSION for this package only
FVER="$VERSION"; VERSION="${TEST_VERSION:-$(. "$ROOT/packaging/repo.conf"; echo "$VERSION")}"
DVER=$(sed -n 's/^PACKAGE_VERSION=//p' "$F/src/driver/dkms.conf")
FS="$ROOT/build/pkg-stage/slate-facetimehd"
rm -rf "$FS"; mkdir -p "$FS/DEBIAN" "$FS/usr/src/facetimehd-$DVER" "$FS/usr/share/slate-facetimehd" "$FS/usr/sbin" "$FS/etc/modprobe.d"
cp -a "$F/src/driver/." "$FS/usr/src/facetimehd-$DVER/"
install -m644 "$F/src/firmware/facetimehd-firmware-install.sh" "$F/src/UPSTREAM" "$FS/usr/share/slate-facetimehd/"
install -m755 "$F/slate-facetimehd-firmware" "$FS/usr/sbin/"
echo "blacklist bdc_pci   # the camera's PCI ID is claimed by bdc_pci otherwise" > "$FS/etc/modprobe.d/slate-facetimehd.conf"
echo /etc/modprobe.d/slate-facetimehd.conf > "$FS/DEBIAN/conffiles"
chmod -R u+rwX,go+rX,go-w "$FS"
for s in postinst prerm postrm; do sed "s/@DRIVER_VERSION@/$DVER/g" "$F/$s" > "$FS/DEBIAN/$s"; chmod 755 "$FS/DEBIAN/$s"; done
SIZE=$(du -sk --exclude=DEBIAN "$FS" | cut -f1)
sed -e "s/@VERSION@/$FVER/" -e "s/@SIZE@/$SIZE/" "$F/control.in" > "$FS/DEBIAN/control"
FDEB="$PKGOUT/slate-facetimehd_${FVER}_all.deb"
dpkg-deb --root-owner-group -Zxz --build "$FS" "$FDEB" >/dev/null
echo "built $FDEB"
DEBS+=("$FDEB")

# 3. Signed apt repository (keeps older versions in the pool)
mkdir -p "$REPO/pool/main" "$REPO/dists/$SUITE/main/binary-amd64"
for d in "${DEBS[@]}"; do
  if [ -e "$REPO/pool/main/$(basename "$d")" ] && ! cmp -s "$d" "$REPO/pool/main/$(basename "$d")"; then
    echo "NOTE: replacing the already-built $(basename "$d") in repo/. Installs that already have that"
    echo "      version won't get this change; bump the version for anything you publish."
  fi
  cp "$d" "$REPO/pool/main/"
done
cd "$REPO"
apt-ftparchive packages pool > "dists/$SUITE/main/binary-amd64/Packages"
gzip -9nkf "dists/$SUITE/main/binary-amd64/Packages"
apt-ftparchive \
  -o APT::FTPArchive::Release::Origin=Slate -o APT::FTPArchive::Release::Label=Slate \
  -o APT::FTPArchive::Release::Suite="$SUITE" -o APT::FTPArchive::Release::Codename="$SUITE" \
  -o APT::FTPArchive::Release::Architectures="amd64 all" \
  -o APT::FTPArchive::Release::Components=main \
  release "dists/$SUITE" > "dists/$SUITE/Release.tmp"
mv "dists/$SUITE/Release.tmp" "dists/$SUITE/Release"
rm -f "dists/$SUITE/InRelease" "dists/$SUITE/Release.gpg"
gpg --batch --yes --default-key "$KEYID" --clearsign -o "dists/$SUITE/InRelease" "dists/$SUITE/Release"
gpg --batch --yes --default-key "$KEYID" -abs -o "dists/$SUITE/Release.gpg" "dists/$SUITE/Release"
gpg --export "$KEYID" > slate-archive-keyring.gpg
cp "$ROOT/packaging/join-updates.sh" join-updates.sh
sed -i "s|@REPO_URL@|$REPO_URL|; s|@SUITE@|$SUITE|" join-updates.sh
touch .nojekyll   # GitHub Pages: serve files as-is
echo "repo ready in repo/ (key $KEYID) -> upload it to $REPO_URL"
