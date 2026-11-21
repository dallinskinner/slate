# Slate on the Intel MacBook Pro (A1398)

A1398 = MacBook Pro 15" Retina, mid 2012 to mid 2015. No T2 chip, so the normal Slate ISO
works. It currently runs ChromeOS Flex, which already erased macOS and cannot dual-boot, so
Slate **replaces** ChromeOS Flex on this machine (installer option "Erase disk").

## Hardware support
| Part | Status in Slate |
|---|---|
| Keyboard, trackpad (incl. gestures) | works (bcm5974 / libinput) |
| Retina display | works; Plasma picks a scale (System Settings > Display to adjust) |
| Wi-Fi 2012-2014 (BCM4331 / BCM4360) | `wl` driver from `broadcom-sta-dkms` (in Slate since build 6) |
| Wi-Fi 2015 (BCM43602) | `brcmfmac` + `firmware-brcm80211` (in Slate since build 6) |
| Sound (Cirrus CS4208) | usually works; if not, check `aplay -l` and tell Claude |
| Discrete GPU (NVIDIA 650M/750M, AMD M370X on some) | open drivers (nouveau / amdgpu); fine for desktop use |
| FaceTime HD camera | not supported (needs the out-of-tree facetimehd driver) |

Find the exact year: in ChromeOS Flex open `chrome://system`, search `product_name`
(MacBookPro10,1 = 2012; 11,2/11,3 = 2013-14; 11,4/11,5 = 2015).
In Slate's live session, `lspci -nn | grep -i net` shows the Wi-Fi chip.

## Steps
1. Back up anything in ChromeOS Flex's local **Downloads** (and Linux files, if used).
   Everything else is in the Google account.
2. Plug in the Slate USB, power on while holding **Option (⌥)**, pick **EFI Boot**.
3. Try the live session first: Wi-Fi, keyboard, trackpad, sound, screen. Nothing is changed
   on the Mac yet.
4. Install Slate > Partitions: **Erase disk**, and check the selected disk is the Mac's
   internal SSD (about 128-512 GB, **not** the USB stick).
5. After install it should boot straight into Slate. If it boots to a folder-with-question-mark
   or back into the USB, hold **Option** and pick **EFI Boot**, then tell Claude (we can make
   it permanent with a fallback boot file, which is safe on a Slate-only disk).
