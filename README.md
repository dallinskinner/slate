# Slate

**A calm, fast desktop built on Debian.** Website: https://dallinskinner.github.io/slate

Slate is a Debian 13 (trixie) based Linux OS for x86_64 PCs and Intel Macs, shipped as a hybrid
ISO (UEFI + BIOS) you can try from a USB stick and install next to Windows. The desktop is KDE
Plasma styled to feel like ChromeOS: a floating bottom shelf, round app icons and overlapping
windows, in dark gray with a lime accent (`#b6f23a`).

## Releases
Each release is named after a stone or mineral, in alphabetical order, and gets its own ASCII-art
rock (wallpaper, welcome animation, terminal logo):
0.1 Agate → **0.2 Basalt** (current) → Cobalt → Dolomite → Emerald → Flint → Granite → Hematite →
Jade → Kyanite → Lapis → Marble → Obsidian → Pumice → Quartz.

**Basalt adds:**
- Slate updates through Discover: the Slate look ships as the `slate-desktop` package from the
  [Slate update server](https://github.com/dallinskinner/slate-updates).
- A welcome animation on first login and after each upgrade, then quick setup (light/dark,
  accent color, wallpaper).
- A styled boot menu.
- A Slate Konsole theme, and the `slate` command (system info with the release rock).
- Optional MacBook FaceTime HD camera support.

Agate installs switch to updates once:
`curl -fsSL https://dallinskinner.github.io/slate-updates/join-updates.sh | sudo sh`

## Apps
| | App | Shortcut |
|---|---|---|
| Launcher (app grid) | Kickoff | Meta (Windows key) |
| Browser (default) | Brave (from Brave's apt repo) | Meta+B |
| Files | Dolphin | Meta+E |
| Terminal | Konsole | Ctrl+Alt+T |
| App store / updates | Discover | |
| Screenshots | Spectacle | Print |
| Images / PDFs / archives / calculator | Gwenview / Okular / Ark / KCalc | |
| Video + music | mpv | |
| Installer (live USB) | Calamares ("Install Slate" on the desktop) | |

## Customize
- **Global Theme:** Slate (dark) or Slate Light. **Accent:** lime, cyan, orange or violet (folders follow).
- **Wallpapers:** one rock per release (Slate Agate, Slate Basalt) plus Slate, Hatch, Big S, Glow, Mono and Light.
- Replay the welcome and quick setup any time: "Welcome to Slate" in the launcher, or `slate welcome`.

## Build
On Debian or Ubuntu:

    sudo apt install debootstrap debian-archive-keyring xorriso ./tools/live-build_20250505+deb13u1_all.deb
    ./scripts/build-iso.sh          # -> build/slate-0.2-basalt-amd64.hybrid.iso (~2.8 GB)
    sudo apt install qemu-system-x86 ovmf
    ./scripts/test-vm.sh            # boot it in a VM with a throwaway disk

## Layout
| Path | What |
|---|---|
| `overlay/` | Everything Slate adds to the system; becomes the `slate-desktop` package. Look-and-feel (shelf layout, splash), color schemes, icon theme, wallpapers, Plymouth, GRUB theme, SDDM/KWin/Konsole/GTK defaults, Slate Welcome (`usr/lib/slate-welcome`), `slate` command. |
| `live-overlay/` | Live-USB-only files (live session tweaks, Brave's apt source). |
| `config/package-lists/` | Debian packages in the image. |
| `hooks/` | Build hooks: Brave install, slate-desktop install, installer naming. |
| `installer/calamares/` | Calamares settings and Slate branding (dual-boot safe). |
| `bootloaders/` | Live USB boot menu. |
| `branding/` | Logo, `ascii_rocks.py` (the release rocks), `build-assets.py` (wallpapers, icons, splash, GRUB theme), `build-kde-theme.py` (colors, Konsole theme). Re-run after changing the logo or palette. |
| `packaging/` | `slate-desktop` maintainer scripts, `slate-facetimehd` (camera driver), update-server config. |
| `scripts/` | `build-iso.sh`, `build-packages.sh`, `publish-updates.sh`, `test-vm.sh`. |
| `website/` | The website (static; published to the `gh-pages` branch). |
| `docs/` | Dual-boot notes, Intel Mac guide, how updates work. |
| `asahi/` | Apple Silicon path (on hold). |

## Credits
Built on [Debian](https://www.debian.org) and [KDE Plasma](https://kde.org/plasma-desktop/);
not affiliated with either. Round icons from Numix Circle; font Hack. The FaceTime HD driver is
[patjak/facetimehd](https://github.com/patjak/facetimehd) (GPL-2.0).
