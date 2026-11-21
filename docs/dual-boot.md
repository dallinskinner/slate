# Dual booting with macOS on an M1 MacBook

1. Back up with Time Machine. Resizing a disk can fail.
2. Update macOS to a version listed in `supported_fw` in `asahi/installer_data.json`.
3. Host `utmos-asahi.zip` + `installer_data.json` on a web server you control.
4. In macOS Terminal, run the Asahi installer pointed at your hosted files (see the asahi-installer
   docs for the env var that overrides the OS list) and follow the prompts: pick free space to shrink
   macOS into, choose UTMOS. macOS partitions are shrunk, never erased.
5. Shut down when told. Boot by holding the power button until the startup picker appears, then pick UTMOS.
6. To remove: boot macOS, use the Asahi uninstall steps from the Asahi docs, then reclaim the space.

Test the installer UX first in UTM with the generic ISO. UTM cannot test the Asahi boot chain.
