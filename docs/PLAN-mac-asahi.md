# Plan: Custom OS built on Fedora Asahi Remix (dual boot on M1 MacBook)

## Context
Goal: our own Linux-based OS, dual-booted next to macOS on the user's M1 MacBook. Earlier plan used Debian plus a hand-rolled Asahi package. That was dropped: Debian has no Asahi kernel/boot packages, so we'd have to build the kernel, m1n1 and U-Boot ourselves. Instead we **build on Fedora Asahi Remix** (the best-supported Asahi distro) and customize it.

The user's Mac has only ~19 GB free disk (96% full). That must be fixed before any install.

## Approach
Two stages:
1. **Stage A: install stock Fedora Asahi Remix** with the official installer (`curl https://alx.sh | sh` in macOS Terminal). Confirms dual boot works on this Mac before we invest in customization.
2. **Stage B: customize and re-package.** Layer our own OS on top: branding, package set, config, apps. Produce our own installable OS package for the Asahi installer, built from Fedora Asahi Remix's image sources.

We depend on the Asahi project for the kernel, m1n1, U-Boot and GPU driver. We do not rewrite those.

## Steps
1. **Free disk space** on macOS: target 50+ GB free (system needs ~30-50 GB). Back up with Time Machine first.
2. **Stage A install.** Run the Asahi installer, shrink macOS, choose Fedora Asahi Remix (KDE or minimal variant), reboot, verify Wi-Fi, display, audio, GPU. Document in `docs/dual-boot.md` (rewrite it for this path).
3. **Repo restructure** (replaces the Debian layout):
   - Remove: `config/` (live-build), `scripts/build-iso.sh`, `scripts/build-asahi.sh`, `installer/` (Calamares), Debian package list.
   - Keep: `README.md` (rewritten), `docs/`, `kernel/virtio.config` only if a UTM test target is still wanted, otherwise remove.
   - Add: `overlay/` (files for `/etc`, skel, branding), `packages/` (RPM spec files for our own packages, e.g. `utmos-release`, `utmos-branding`, `utmos-settings`), `image/` (build descriptions for the Remix image), `scripts/`.
4. **Our own packages.** Write RPMs: `utmos-release` (os-release, issue, name), `utmos-branding` (logo, wallpaper, boot splash), `utmos-settings` (default configs, package group). Build with `rpmbuild`/`mock` in a Fedora environment, either on the installed Fedora Asahi system itself (no VM needed once Stage A is done) or in a Fedora container.
5. **Image build.** Look at the `fedora-asahi-remix` GitHub org for its image descriptions (kiwi-based) and installer metadata. Fork or reference those, add our RPMs and package set, build the image on the installed Fedora Asahi system (arm64 native). Output: ESP files + root image + `installer_data.json` in the Asahi installer's OS-package format. Confirm the format from the current `asahi-installer` repo; do not rely on memory.
6. **Host and install.** Host the package, run the Asahi installer pointing at it (verify the exact override option in asahi-installer docs), install as a second Linux OS or replace the stock Remix install.
7. **Iterate.** Add the apps and desktop customization the user wants once the base boots.

## Verification
- Stage A: boots from the macOS startup picker (hold power button); Wi-Fi, display, audio and GPU work; macOS still boots.
- Each RPM builds and installs cleanly (`rpm -qip`, `dnf install`) and shows branding in `/etc/os-release`.
- Image build produces a package whose layout matches the real installer's format; verify by running the installer against it. A real-Mac install needs a backup first, and nothing is claimed working until it boots.

## Open risks
- Disk space on the Mac (see step 1).
- Fedora Asahi Remix's image tooling may change; check the upstream repos before depending on the layout.
- A bad install can leave a stale boot entry. Document the Asahi uninstall steps.
- Asahi on M1 does not support everything (e.g. Touch ID, some power features); set expectations.
