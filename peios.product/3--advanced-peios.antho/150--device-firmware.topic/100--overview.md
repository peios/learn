---
title: Device firmware
type: concept
description: "Why some hardware needs a firmware package before it works, how Peios splits linux-firmware into firmware-<family> packages, what license_class = firmware means, and what is deliberately not shipped."
related:
  - peios/package-management/overview
  - peios/linux-compatibility/overview
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/disks-and-filesystems/stable-device-names
---

Many devices carry no firmware of their own: the driver has to upload a
vendor-supplied blob into the device before it does anything. Almost every
Wi-Fi adapter works this way, as do modern GPUs (AMD, Intel, NVIDIA), many
Ethernet controllers, laptop audio codecs and amplifiers, and Bluetooth.
Without the blob the driver loads, finds the device, asks the kernel for a
file under `/usr/lib/firmware/`, and — if it is not there — gives up. The
symptom is a device that is *present* (`lspci` lists it, the module is
loaded) but never comes up, and a line in `dmesg` like
`firmware: failed to load iwlwifi-so-a0-gf-a0-89.ucode (-2)`.

The kernel loads firmware itself. There is no daemon and no udev step
involved: the driver's request is answered from the filesystem, transparently
decompressing the `.zst` files Peios ships. That makes firmware a packaging
matter — the right file in the right place — and this page is about which
package that is.

## The `firmware-<family>` packages

Upstream collects device firmware in one tree, `linux-firmware`, which is
over a gigabyte and mostly for hardware Peios does not run on. Peios does not
ship it whole. One recipe builds it into packages by vendor or driver
family, each carrying only that family's blobs and only that family's
licence texts:

| Package | Covers |
|---|---|
| `firmware-iwlwifi` | Intel Wi-Fi |
| `firmware-atheros` | Qualcomm Atheros Wi-Fi and Bluetooth (ath9k, ath10k/11k/12k, btqca) |
| `firmware-mediatek` | MediaTek Wi-Fi and Bluetooth (mt76, mt79xx) |
| `firmware-realtek` | Realtek Wi-Fi, Bluetooth, USB/PCIe Ethernet |
| `firmware-broadcom` | Broadcom and Cypress Wi-Fi, Bluetooth, tg3/bnx2 Ethernet |
| `firmware-marvell` | Marvell and NXP Wi-Fi and Bluetooth (mwifiex, libertas) |
| `firmware-ralink` | Ralink rt2x00 Wi-Fi |
| `firmware-amd-graphics` | AMD Radeon GPUs (amdgpu, radeon) |
| `firmware-amd-platform` | AMD PSP/SEV, Platform Management Framework, XDNA NPU |
| `firmware-intel-graphics` | Intel GPUs (i915, xe: GuC, HuC, DMC) |
| `firmware-intel-platform` | Intel Bluetooth, sensor hub, IPU cameras, NPU, QAT, E800 NICs |
| `firmware-intel-sound` | Intel audio DSP firmware for pre-2019 parts (AVS, catpt, Skylake SST) |
| `firmware-intel-sof` | Intel Sound Open Firmware — the audio DSP firmware and topologies for Ice Lake and newer (from SOF's own release, not linux-firmware) |
| `firmware-nvidia-graphics` | NVIDIA GPUs for nouveau/nova (GSP) |
| `firmware-audio-codecs` | Cirrus, TI and Creative laptop codecs and amplifiers |
| `firmware-nic` | Wired NICs: Chelsio, QLogic qed, Myricom, Tehuti, 3Com, legacy USB Ethernet |
| `firmware-storage` | FC/SCSI HBAs (qla2xxx, QLogic BR, AdvanSys) and the ENE card reader |
| `firmware-misc` | USB serial adapters, DVB/V4L tuners, legacy Wi-Fi, PCMCIA, sound cards |

Which ones a machine needs is a question about its hardware, and the
answer is usually two or three: an Intel laptop wants `firmware-iwlwifi`,
`firmware-intel-graphics`, `firmware-intel-platform` (Bluetooth),
`firmware-intel-sof` (audio DSP) and `firmware-audio-codecs`; an AMD one swaps the graphics and platform
packages. `dmesg | grep firmware` after boot names every file a driver asked
for and did not get, and the file's directory (`intel/`, `amdgpu/`,
`rtw89/`) maps onto the table.

Every package installs under `/usr/lib/firmware/`, which is where the kernel
looks (it reads `/lib/firmware`, and `/lib` is a view of `/usr/lib`). The
blobs are zstd-compressed on disk; the kernel decompresses them on load and
no tool needs to know.

## Licensing, and `license_class = "firmware"`

Firmware blobs are almost never free software. Vendors permit
redistribution of the unmodified binary and nothing more, each under their
own terms, and there is no source. Peios does not pretend otherwise: each
`firmware-<family>` package declares its vendor licence as a `LicenseRef-`
SPDX expression, ships the licence text under
`/usr/share/licenses/firmware-<family>/`, and carries
`license_class = "firmware"` in its manifest.

That class is the machine-readable fact. `peipkg info firmware-iwlwifi`
shows it, a composed image's `/usr/share/licenses.json` lists it for every
package, and it is what lets a tool answer "what non-free is on this
machine" without parsing licence expressions. `firmware` is a class of its
own — distinct from `proprietary` — because it is a different bargain: it
does not run on the CPU, it is needed to use hardware you already own, and
you cannot get it any other way. Peios ships firmware and does not ship
proprietary userspace; the class is how an image policy can say exactly
that.

## Trust

Firmware runs on a device that can DMA into host memory, so a tampered
blob is a compromise of the whole system — at least as bad as an unsigned
binary running with kernel privilege, and it happens without an exec for
the kernel to intercept. Peios treats firmware as part of the trusted
computing base and signs it the same way it signs TCB binaries.

Every blob in every `firmware-<family>` package carries an ML-DSA-65
signature made with the TCB key when the package is built. Blobs are not
ELF, so the signature travels as a `<blob>.peios.sig` entry beside the
blob in the package, and `peipkg` turns it into the file's
`security.peios.sig` extended attribute as it installs the blob (see
[Signature format](~peios/binary-signing/signature-format)). The kernel
verifies that attribute every time a driver asks for firmware, on the
exact bytes it is about to hand to the device, and refuses a file that is
unsigned, altered, or signed with a key below the TCB tier. The signature
covers the compressed `.zst` bytes as they sit on disk, so verification
happens before decompression.

In 2026.8 the check runs in **log** mode: a file that would be refused is
reported to the kernel log and still loaded, so a system can be brought
up on a mixed firmware set and the gaps found. Refusal becomes the
default in the release after the whole farm has shipped signed; until
then `kacs_fwsig=enforce` on the kernel command line turns it on for a
boot, and `kacs_fwsig=log` turns it back off. Either
way, `/usr/lib/firmware` is not a place to put files by hand: an unsigned
blob dropped there, or one placed on a path added to the loader's search
list, is exactly what the check exists to catch.

## What is not shipped

The upstream tree also carries firmware for ARM SoCs (Qualcomm, MediaTek
video processors, Rockchip, Amlogic, NXP i.MX), datacentre switches and
SmartNICs (Mellanox, Netronome), InfiniBand and crypto accelerators. None
of it is packaged: Peios is x86-64, and a family is only added when there is
hardware to use it. CPU microcode is a separate mechanism entirely —
`intel-ucode` and `amd-ucode` are early-loaded from the initramfs before the
firmware loader exists.

Nothing under `/usr/lib/firmware` is needed to reach a root filesystem
(NVMe, AHCI, USB and virtio storage need no blobs), so the initramfs carries
no firmware. A driver that probes in the initramfs and cannot find its
blob is re-probed once the real root is mounted and the device manager
replays device events.

**Intel Sound Open Firmware** is not in linux-firmware at all; it is a
separate upstream (thesofproject's `sof-bin`), which is why it is its own
package, `firmware-intel-sof`, rather than a family of the linux-firmware
recipe. Only the Intel-signed images ship — the `community` builds signed
with the public development key run only on Chromebooks and development
boards whose DSPs accept that key.
