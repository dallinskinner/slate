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
# BOOT=disk starts the installed system; default is the ISO (live session)
if [ "${BOOT:-cd}" = disk ]; then HD_FIRST=0; CD_FIRST=1; else HD_FIRST=1; CD_FIRST=0; fi
cp -n /usr/share/OVMF/OVMF_VARS_4M.fd vm/OVMF_VARS.fd 2>/dev/null || true
qemu-system-x86_64 -enable-kvm -m 4096 -smp 4 -cpu host \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=vm/OVMF_VARS.fd \
  -drive file="$DISK",if=none,id=hd -device virtio-blk-pci,drive=hd,bootindex=$HD_FIRST \
  -drive file="$ISO",media=cdrom,if=none,id=cd -device ide-cd,drive=cd,bootindex=$CD_FIRST \
  $GFX \
  -device qemu-xhci -device usb-tablet \
  -nic user,model=virtio-net-pci \
  -monitor unix:vm/qemu-monitor.sock,server,nowait
