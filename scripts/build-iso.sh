#!/usr/bin/env bash
# Build the Slate x86_64 (amd64) hybrid ISO (UEFI + BIOS).
# Uses Debian's upstream live-build (tools/live-build_*_all.deb), NOT Ubuntu's
# live-build package, which is an old fork that cannot build current Debian.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD

if ! lb --version 2>/dev/null | grep -q '^20'; then
  echo "Need Debian's live-build. Install with:"
  echo "  sudo apt install debootstrap debian-archive-keyring xorriso ./tools/live-build_20250505+deb13u1_all.deb"
  exit 1
fi

# Slate's own files ship as the slate-desktop package (so installs get updates).
. packaging/repo.conf
case "$REPO_URL" in *REPLACE-ME*)
  echo "Set REPO_URL in packaging/repo.conf first (the update server; see docs/updates.md)."
  exit 1 ;;
esac
./scripts/build-packages.sh
DEB="$ROOT/build/packages/slate-desktop_${VERSION}_all.deb"

sudo -v   # ask for the password once, up front
BUILD=build; mkdir -p "$BUILD"; cd "$BUILD"
# A failed build can leave bind mounts inside chroot/ (proc, sys, dev, config...),
# which makes `lb clean` fail with "Read-only file system". Unmount them first,
# deepest first, and only ones inside this build directory.
{ findmnt -rn -o TARGET | grep -F "$PWD/chroot" || true; } | sort -r | while read -r m; do
  echo "unmounting leftover $m"; sudo umount -l "$m"
done
sudo lb clean || true   # keeps cache/ (downloaded packages); use --purge to wipe it
lb config \
  --mode debian \
  --architectures amd64 \
  --distribution trixie \
  --archive-areas "main contrib non-free non-free-firmware" \
  --mirror-bootstrap http://deb.debian.org/debian/ \
  --mirror-binary http://deb.debian.org/debian/ \
  --binary-images iso-hybrid \
  --bootloaders "grub-efi,grub-pc" \
  --debian-installer none \
  --iso-application "Slate 0.2 Basalt" \
  --iso-volume "SLATE" \
  --image-name slate-0.2-basalt \
  --bootappend-live "boot=live components quiet splash hostname=slate username=slate user-fullname=Slate"

# Start from a clean copy of our files each build (cp only adds; stale files from
# earlier builds, e.g. old configs or hooks, would otherwise end up in the image).
rm -rf config/includes.chroot config/bootloaders
rm -f config/hooks/normal/0[0-9][0-9][0-9]-*.hook.chroot   # ours are 0100-0999; live-build's start at 1000
cp -r "$ROOT"/config/package-lists/. config/package-lists/
mkdir -p config/includes.chroot
cp -r "$ROOT"/live-overlay/. config/includes.chroot/       # live/ISO-only files
install -Dm644 "$DEB" config/includes.chroot/root/slate-desktop.deb   # installed by hooks/0300
mkdir -p config/includes.chroot/etc/calamares
cp -r "$ROOT"/installer/calamares/. config/includes.chroot/etc/calamares/
rm -f config/archives/brave.*   # (old location; Brave now comes from hooks/0200-brave)
mkdir -p config/bootloaders
cp -r "$ROOT"/bootloaders/. config/bootloaders/
mkdir -p config/hooks/normal
cp "$ROOT"/hooks/*.hook.chroot config/hooks/normal/

# stdin from /dev/null: no terminal attached, so sudo makes no pty and the build
# cannot get job-control-stopped (it froze for hours in apt-get with `| tee`).
sudo lb build </dev/null 2>&1 | tee build.log
ls -lh ./*.iso
