# Asahi package

`scripts/build-asahi.sh` produces `utmos-asahi.zip` (ESP files + `root.img`) and `installer_data.json`.

UNVERIFIED: the JSON schema is written from memory of the Asahi installer's format, and the
`/usr/lib/asahi-boot` path is a placeholder. Check both against the current `AsahiLinux/asahi-installer`
repo (`installer_data.json` examples, `package/` layout) before trusting a build.

Debian has no official linux-asahi / m1n1 / u-boot-asahi packages: you must build or source them.
That is the hardest open task. If it stalls, switch the base to Fedora Asahi Remix as the plan allows.
