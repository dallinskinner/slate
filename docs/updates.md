# Slate updates

Since Slate 0.2 (Basalt), Slate's own files (themes, wallpapers, icons, boot splash, login look,
GRUB defaults, default apps, os-release) ship as one package, **slate-desktop**, built from
`overlay/`. Installs get new versions from the Slate update server through normal updates
(Discover, or `sudo apt update && sudo apt full-upgrade`), the same way as Debian and Brave updates.

## Pieces
| What | Where |
|---|---|
| Package contents | `overlay/` (+ `branding/slate-logo.svg`, apt source, public key) |
| Maintainer scripts | `packaging/slate-desktop/` (os-release divert, Plymouth theme, update-grub, Meta+B trigger) |
| Server address, version | `packaging/repo.conf` (`REPO_URL`, `VERSION`) |
| Signing key (PRIVATE) | `packaging/gnupg/`: **back it up** (e.g. to a USB stick). Never upload it. Lose it and installs can't verify new updates. |
| Signed apt repo | `repo/` (made by `scripts/build-packages.sh`), a git checkout of github.com/dallinskinner/slate-updates, served by GitHub Pages at https://dallinskinner.github.io/slate-updates |
| ISO-only files | `live-overlay/` (live-session tweaks, Brave's apt source) |

## Publish an update
1. Change files in `overlay/` (or run the `branding/` generators).
2. Bump `VERSION` in `packaging/repo.conf` (0.2.0 -> 0.2.1; a new release like Cobalt -> 0.3.0).
3. `./scripts/publish-updates.sh` (builds, signs, commits and pushes `repo/`; needs `gh auth login` once).
Installs see it on their next update check. Users' own settings (`~/.config`) win over the new
defaults, so a changed default wallpaper only shows for people who never picked one.

## Agate (0.1) installs
They predate the package. One-time, in Konsole:
`curl -fsSL https://dallinskinner.github.io/slate-updates/join-updates.sh | sudo sh`

## Tested (2026-11-21)
On a throwaway copy of the Agate system: join -> 0.2.0 (os-release diverts taken over, `/etc/os-release`
back to a symlink, Plymouth theme, Meta+B file), upgrade to 0.2.1 (changed conffile installed),
remove (Debian os-release restored), reinstall.
