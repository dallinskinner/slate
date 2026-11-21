#!/usr/bin/env bash
# Package a Debian arm64 rootfs as an Asahi-installer OS package. Run on arm64 Linux as root.
# Needs: debootstrap, e2fsprogs, zip. Asahi kernel/m1n1/u-boot packages must be supplied (see asahi/README.md).
set -euo pipefail
cd "$(dirname "$0")/.."
ASAHI_PKGS="${ASAHI_PKGS:?set ASAHI_PKGS to a directory of linux-asahi, m1n1, u-boot-asahi .debs}"
OUT=build/asahi; ROOT=$OUT/rootfs
rm -rf "$OUT"; mkdir -p "$ROOT" "$OUT/pkg/esp"
debootstrap --arch=arm64 stable "$ROOT" http://deb.debian.org/debian
cp -r overlay/. "$ROOT"/
cp "$ASAHI_PKGS"/*.deb "$ROOT/tmp/"
chroot "$ROOT" sh -c 'xargs -a /dev/stdin apt-get install -y' < config/package-lists/base.list.chroot
chroot "$ROOT" sh -c 'dpkg -i /tmp/*.deb && rm /tmp/*.deb'
# ESP contents (m1n1 + U-Boot + GRUB) come from the m1n1/u-boot packages installed above:
cp -r "$ROOT"/usr/lib/asahi-boot/. "$OUT/pkg/esp/" 2>/dev/null || echo "WARN: no /usr/lib/asahi-boot in rootfs; ESP is empty"
truncate -s 6G "$OUT/pkg/root.img"; mkfs.ext4 -d "$ROOT" -L utmos-root "$OUT/pkg/root.img"
(cd "$OUT/pkg" && zip -r ../utmos-asahi.zip .)
cp asahi/installer_data.json "$OUT/"
echo "Done: $OUT/utmos-asahi.zip + $OUT/installer_data.json"
