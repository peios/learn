---
title: Quick start
type: how-to
description: Build the Experimental medium from a four-line spec and boot it under QEMU — no root, one command.
related:
  - peios/peiso/building-images/overview
  - peios/peiso/building-images/running-a-build
  - peios/peiso/reference/the-spec
---

This page builds the Peios Experimental medium and boots it. It assumes a checkout of the Peios tree with a populated signed package repository (`pkgs/_repo2_`), which supplies the edition and its closure.

## What you need on the build host

- **peiso**, built from `peiso/` in the tree (`go build -o peiso .`), or on your PATH.
- **squashfs-tools**, **xorriso**, **dosfstools** and **mtools** — the host-side packers. Everything Peios-specific (the initramfs and UKI tools) is taken from the root being built.
- For booting: **QEMU** with KVM and the **OVMF** firmware.

No root. If any step asks for it, that is a bug.

## The spec

`dist/release/experimental.toml`:

```toml
[[packages.repository]]
url = "file://../../pkgs/_repo2_"
trust_anchors = ["63977c7be45624999b88bac5aa55ab5280656ee076617a285c87602a0d980602"]
keys = ["../../pkgs/dev-signing.pub"]

[baseline]
edition = "Experimental"
package = "dev.peios.peios-experimental"
source_date = "2026-06-22T00:00:00Z"
```

The explicit package selects `dev.peios.peios-experimental`; without a version,
the newest available version wins. The trust anchor authenticates repository
metadata, and `keys` supplies the package-signing public key. [The
spec](~peios/peiso/reference/the-spec) lists every key.

## Build

```sh
cd dist/release
make iso
```

peiso reports each stage:

```text
resolving peios-experimental
resolved dev.peios.peios-experimental 2026.8-1 (… packages)
composing dist/peios-experimental-2026.8/root
resolving medium packages
publishing dist/peios-experimental-2026.8/repo
medium repo: 2 packages, trust anchor 6e50…
staged seed authd-policy
…
seeds: 15 staged
packing initramfs -> …/root/system/boot/initramfs.cpio.zst
squashing root -> …/rootfs.squashfs
squashed with 4414 signature attribute(s)
building UKI -> …/root/boot/efi/EFI/BOOT/BOOTX64.EFI
building ISO -> dist/peios-experimental-2026.8/peios-experimental-2026.8.iso
dist/peios-experimental-2026.8/peios-experimental-2026.8.iso
```

The last line is the ISO. Everything the build made is beside it, in `dist/peios-experimental-2026.8/` — see [Running a build](~peios/peiso/building-images/running-a-build) for the layout.

## Boot

```sh
make boot
```

runs QEMU with UEFI firmware, the ISO attached as a virtio disk, and the serial console on your terminal. You will see the kernel, then `prelude` (the initramfs PID 1) running its hooks — `live-boot` finds the medium and mounts the live root — then `peinit` bringing up the services the release's seeds define, and finally a login prompt. The image autologs in a development account.

### Open the web desktop

`make iso` includes GXWI, the Fenestra compositor, the fenesh desktop shell,
Gexora file explorer and the Hello demonstration app. Their packages supply
binaries, application declarations, icons and registry seeds; no development
share or checkout is needed in the guest.

After `make boot` reaches the console, open **https://127.0.0.1:7780/** on the
host. The live image has the `peios` development account with no password.
Fenestra and its apps run as the logged-on principal using a `RemoteInteractive`
session. Installed systems use their provisioned account instead.

GXWI serves **HTTPS** with a certificate the machine makes for itself, so the
browser warns before the first sign-in. Before going past the warning, check
the certificate's SHA-256 fingerprint against the machine's own: sign in at the
VM's console (the live image's `peios` account has no password) and run
`cat /var/state/gxwi/certificate.sha256`. A live medium makes a new key
every boot, so the warning comes back each time. `installerd` attempts to carry
the key into the installed system, but a skipped or failed transfer does not
fail the installation. Verify any changed fingerprint through the installed
machine's trusted console before entering credentials. See
[certificate carry-over](~peios/signing-in-from-a-browser/the-certificate#installation-and-first-boot).
Plain `http://` is answered with a redirect to `https://` and nothing else.

The Experimental edition enables TCP 7780 on all guest interfaces and admits it
through the guest packet policy. The Makefile's host port forwards bind to
localhost; that protects the QEMU host listener, not a machine booted directly
from the ISO or a VM configured with bridged networking.

The edition opts into `gxwid-service`, `gxwi-config`, `gxwi-network`,
`fenestra-config` and `fenesh-config`. `Machine\Software\GXWI` selects the
listener and compositor; `Machine\Software\Fenestra` selects the shell.
Package installation alone does not activate these policy seeds.
The GXWI service retains `SeImpersonatePrivilege` so it can hand the authenticated
principal's token to peinit for the session job.

SSH remains available on host port 2222 after provisioning a permitted key or
password credential. GXWI does not currently offer SSH-key authentication.

The same Makefile has `boot-dwe`, `boot-install` and `boot-installed`; [Running a build](~peios/peiso/building-images/running-a-build) covers them.

## Change something

Two things are yours to change in the spec without touching anything else:

```toml
[devtools]
dwe = true            # a development medium; builds to …-2026.8-dwe/

[registry]
remove = ["lpsd-first-account"]   # drop a seed the release would apply
add    = ["my-service"]           # add one a package in the closure ships

[[package]]
name = "org.gnu.bash"             # carry a package the edition does not
```

To change *what the release is*, change the edition package
(`pkgs/dev.peios.peios-experimental/`) and republish it; the spec does not
change. [Editions](~peios/peiso/editions-and-upgrades/editions) explains why
that line is drawn where it is.
