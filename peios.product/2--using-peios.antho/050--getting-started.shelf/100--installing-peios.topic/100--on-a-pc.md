---
title: Installing on a PC
type: how-to
description: Put Peios on a physical machine. Write the medium to a USB stick, set the firmware up, boot it live, install to the internal disk, and remove the stick before the first restart.
related:
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/first-boot-setup
  - peios/signing-in-from-a-browser/the-certificate
  - peios/device-firmware/overview
  - peios/networking/the-net-command
---

This page covers installing Peios on a physical PC, start to finish. You write the medium to a USB stick, boot the machine from it, look around the live system, and install it to the machine's own disk. Each step links to the page that explains it properly. This page is the order to do them in, plus the things a physical machine does that a virtual machine does not.

## What you need

- **An x86-64 PC with UEFI firmware.** Peios boots through UEFI only, with no legacy BIOS mode, and any PC from the last ten years has UEFI.
- **A USB stick of 2 GB or more that you can erase.** Writing the medium replaces everything on the stick.
- **The Peios medium**, an `.iso` file. To make one yourself, see [the peiso quick start](~peios/peiso/building-images/quick-start).
- **A wired network connection**, if you can. Peios drives the machine's Wi-Fi hardware but cannot join a wireless network yet, so a cable is the only way onto the network for now. Setup does not need a network, but installing from a browser does.
- **A screen and keyboard** for the first boot. After that, another device with a browser on the same network is all you need.

## Write the medium to a USB stick

The `.iso` is a disk image, and it has to be written to the stick byte for byte. Copying the file onto a stick that already has a filesystem does not work.

> [!WARNING]
> **Ventoy and similar multi-ISO tools do not work.** They keep the `.iso` as a file on the stick's own filesystem, and rely on recognising the distribution to patch its initramfs. Peios looks for its medium as a whole disk carrying an ISO9660 filesystem with `rootfs.squashfs` on it. A Ventoy stick has no such disk, so the boot stops at `no boot medium carrying /rootfs.squashfs found`.

On Linux, find the stick by its size and model, and confirm that it is the removable one (`RM` is `1`):

```sh
lsblk -o NAME,SIZE,TRAN,MODEL,RM
```

Then write it, naming the stick by its stable identifier rather than `/dev/sdX`. The letters can change between plugging in and writing, and the identifier cannot:

```sh
ls -l /dev/disk/by-id/ | grep usb
sudo dd if=peios.iso of=/dev/disk/by-id/usb-<the stick> bs=4M oflag=direct conv=fsync status=progress
```

Unmount the stick's old filesystem first if your desktop mounted it. If it stays mounted while you write, the kernel can later write the old filesystem's pending changes back over the image.

On another system, use any tool that writes an image raw. Some tools call this "DD mode" or "image mode", and offer it beside a mode that copies files. Choose the raw one.

## Set up the firmware

Enter the machine's firmware setup at power-on. The key is usually **Del** or **F2**, and the screen says which for a moment as the machine starts.

- **Turn Secure Boot off.** The Peios boot image is not signed with a key that a PC's firmware trusts out of the box, so with Secure Boot on, the firmware refuses to start it.
- **Note the one-time boot menu key**, often **F7**, **F11** or **F12**. It lets you choose the USB stick for this boot without changing the permanent boot order.

Leave the storage controller mode alone unless the installer cannot see your disks. If it cannot, it says so: it names a storage controller that no driver has claimed. The usual cause is a **RAID** or **Intel RST** mode in the firmware, and setting the controller to **AHCI** is the way out.

## Boot the live system

Plug in the stick, power on, and choose it from the boot menu. If it is listed twice, choose the entry marked **UEFI**.

The kernel is quiet by default. What you will see is mostly the initramfs steps, each reporting as it goes. The one that matters on a physical machine is:

```text
OK live-boot: mounted boot medium /dev/sdb at /mnt/medium
```

Then the services start, and the console offers a login. The live system has a `peios` account with no password.

Two commands tell you how the machine looks to Peios:

```sh
lspci          # the hardware: network, graphics, storage controllers
net status     # each network interface, and the address it was given
```

A wired interface showing `readiness routed` and an `address` is on the network. A wireless interface showing `down, no-carrier` is expected, because Wi-Fi is not joined yet. Its presence still means the driver and its [firmware](~peios/device-firmware/overview) loaded.

### If the boot stops

| What you see | What it means |
|---|---|
| The firmware will not start the stick, or reports a security violation | Secure Boot is still on. |
| `no boot medium carrying /rootfs.squashfs found after 50 attempts` | The stick appeared too slowly, or was written as files rather than as an image. Rewrite it with `dd`, or try another USB port. |
| The stick is not offered in the boot menu at all | It is not a UEFI boot device. Check that the image was written raw, and that the firmware is not restricted to legacy boot. |

## Install

With the live system up, open `https://<the address from net status>:7780` in a browser on another device. The browser warns about the certificate. Check the fingerprint against `cat /var/state/gxwi/certificate.sha256` on the machine's console before going on, as [the machine's certificate](~peios/signing-in-from-a-browser/the-certificate) explains. The address opens straight into the installer.

You can also install from the console itself. Both surfaces drive the same installer, and [Installing to disk](~peios/disks-and-filesystems/installing-to-disk) covers the installer, and what it does to the disk, in full.

Choose the machine's internal disk. The stick you booted from is listed, marked, and cannot be chosen. The disk you choose is erased completely, including any other system on it.

> [!IMPORTANT]
> **Remove the USB stick before you press Reboot now.** The installer does not change the firmware's boot order. Many machines try USB before their internal disk, so with the stick still in, the machine starts the medium again and you are back in the installer. Nothing is lost if that happens: pull the stick and restart.
>
> To stop a forgotten stick from taking over a later boot, put the internal disk first in the firmware's boot order. Delete any entries left by the system the disk used to hold while you are there.

## First boot

The installed system starts into [first-boot setup](~peios/disks-and-filesystems/first-boot-setup), on the console and at the same browser address. Setup creates the administrator account and names the machine, and you can give the wired interface a fixed address.

The browser that installed the machine already trusts its certificate, because the installation carries the key across, so setup opens without a second warning.

> [!NOTE]
> If you give the interface your browser is connected through a new address, the setup page in 2026.8 does not follow the machine there under HTTPS. It stays on its starfield. When setup has finished, open the new address yourself. The browser asks about the certificate again, because it trusts a certificate only for the address it was accepted at. It is the same certificate, so the fingerprint is the one you checked before.

When setup finishes, sign in at the machine's address as the account you made.

## Machines known to work

| Machine | Notes |
|---|---|
| Beelink Mini S (Intel Alder Lake-N) | Ethernet (`r8169`), NVMe and USB work without configuration. The Intel Wi-Fi is detected but cannot join a network yet. |
