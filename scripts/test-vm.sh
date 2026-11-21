#!/usr/bin/env bash
# Boot the built ISO in QEMU with UEFI firmware (OVMF) and a throwaway 20G virtual disk.
# Never touches real disks.
set -euo pipefail
cd "$(dirname "$0")/.."
ISO=$(ls -t build/*.iso | head -1)   # newest build
mkdir -p vm
rm -f vm/qemu-monitor.sock   # stale socket from a previous run blocks startup
DISK=vm/test-disk.qcow2
[ -f "$DISK" ] || qemu-img create -f qcow2 "$DISK" 20G
# GL=1 for 3D-accelerated display (faster, but QEMU screendump stops working)
if [ "${GL:-0}" = 1 ]; then GFX="-device virtio-vga-gl -display gtk,gl=on,zoom-to-fit=on"; else GFX="-device VGA,edid=on,xres=1280,yres=800 -display gtk,zoom-to-fit=on"; fi
cp -n /usr/share/OVMF/OVMF_VARS_4M.fd vm/OVMF_VARS.fd 2>/dev/null || true
qemu-system-x86_64 -enable-kvm -m 4096 -smp 4 -cpu host \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=vm/OVMF_VARS.fd \
  -drive file="$DISK",if=virtio \
  -cdrom "$ISO" -boot d \
  $GFX \
  -device qemu-xhci -device usb-tablet \
  -nic user,model=virtio-net-pci \
  -monitor unix:vm/qemu-monitor.sock,server,nowait
