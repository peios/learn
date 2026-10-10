---
title: Install Peios on a PC
type: how-to
description: Prepare a USB medium, choose the correct disk, install Peios on a UEFI PC, and complete the first administrator sign-in.
related:
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/first-boot-setup
  - peios/signing-in-from-a-browser/the-certificate
  - peios/device-firmware/overview
  - peios/networking/the-net-command
---

Use this guide for a fresh installation on a physical PC. At the end, the PC boots from its own disk and you can sign in with the administrator account you created during setup.

If the disk already holds a Peios installation you want to keep, choose [Upgrade an installation](~peios/disks-and-filesystems/installing-to-disk#upgrading-from-the-medium) or [Repair an existing system](~peios/disks-and-filesystems/installing-to-disk#repairing-an-installed-system) instead.

> [!CAUTION]
> Writing the USB medium erases the USB stick. Installing Peios erases the **entire target disk**, including other operating systems and files. Back up anything you need from both devices before starting. The installer does not offer a dual-boot or encrypted-disk layout.

## What you need

- **An x86-64 PC with UEFI firmware.** Legacy BIOS boot is not supported.
- **A USB stick of at least 2 GB** that you can erase.
- **A Peios `.iso` image.** If you need to build one, follow [the peiso quick start](~peios/peiso/building-images/quick-start).
- **A screen and keyboard** for checking the machine, its network address, and its certificate. After setup, you can use another device's browser on the same network.
- **A wired connection for browser access.** Console setup works offline. Peios can detect supported Wi-Fi hardware, but joining a wireless network is not yet available.

Keep the machine on a network you trust while installing and setting it up: the live installer and pending first-boot setup can be opened without signing in.

## Write the medium to a USB stick

Write the `.iso` as a raw disk image. Copying the file onto an existing filesystem does not make a Peios boot medium.

> [!WARNING]
> Ventoy and similar multi-ISO tools are not supported. Peios looks for a whole disk carrying an ISO9660 filesystem with `rootfs.squashfs` on it. A stick that only contains the `.iso` as a file can stop at `no boot medium carrying /rootfs.squashfs found`.

On Linux:

1. Identify the stick by **size, model, USB connection, and removable status** (`RM` is `1`):

   ```sh
   lsblk -o NAME,SIZE,TRAN,MODEL,RM
   ls -l /dev/disk/by-id/ | grep usb
   ```

2. Unmount any of the stick's filesystems that the desktop mounted. Otherwise pending filesystem writes can overwrite part of the new image later.
3. Select the stable identifier for the **whole stick**, not a partition. Replace the placeholder below with the identifier you just checked. Verify the destination again before running `dd`; it overwrites that device.

   ```sh
   sudo dd if=peios.iso of=/dev/disk/by-id/usb-REPLACE_WITH_VERIFIED_STICK_ID bs=4M oflag=direct conv=fsync status=progress
   ```

4. Wait for the command to finish successfully before unplugging the stick.

A stable identifier avoids relying on `/dev/sdX` letters, which can change as devices are attached. It does not replace checking that you selected the right stick.

On another operating system, use a raw image-writing tool. Choose **DD mode** or **image mode** when the tool offers a choice between raw writing and copying files.

## Set up the firmware

Enter firmware setup at power-on; the screen usually names the key, often **Del** or **F2**.

- **Turn Secure Boot off.** The Peios boot image is not signed with a key that PC firmware trusts out of the box.
- **Use UEFI boot.** Note the one-time boot-menu key, often **F7**, **F11**, or **F12**, so you can choose the stick without changing the permanent boot order.
- **Leave the storage-controller mode unchanged unless disks are missing.** If the installer reports an unclaimed RAID, Intel RST, or VMD controller, check the firmware's storage settings. AHCI is the documented alternative. Record the previous setting before changing it; a controller-mode change can affect an existing operating system.

## Boot the live system

Insert the stick and select it from the one-time boot menu. If there are two entries for it, choose the one marked **UEFI**.

During startup, look for a message like this; the device name can differ:

```text
OK live-boot: mounted boot medium /dev/sdb at /mnt/medium
```

A medium with the console installer starts its form. A live login uses the `peios` account with no password. When you have a shell, check the hardware and networking:

```sh
lspci          # network, graphics, and storage controllers
net status     # interfaces and their assigned addresses
```

A wired interface with `readiness routed` and an `address` is on the network. A wireless interface showing `down, no-carrier` is expected while Wi-Fi joining is unavailable; its presence still indicates that the driver and [firmware](~peios/device-firmware/overview) loaded.

The live system keeps changes in memory and discards them at reboot. The current installer copies the shipped image, not your live session's accounts or changes.

### If the boot stops

| Symptom | Check or next step |
|---|---|
| Firmware reports a security violation or refuses to start the stick | Check that Secure Boot is off. |
| `no boot medium carrying /rootfs.squashfs found after 50 attempts` | Check that the image was written raw; rewrite it if needed. If the stick appeared too slowly, try another USB port. |
| The stick is absent from the boot menu | Check the raw image write and that firmware allows UEFI boot rather than only legacy boot. |
| The installer cannot see an internal disk | Look for its unclaimed-controller warning, then check storage-controller mode in firmware. Use **Rescan** after checking the hardware. |

## Install

Use the console form, or open `https://<address-from-net-status>:7780` on another device. Browser installation requires a medium with the [graphical installer enabled](~peios/disks-and-filesystems/installing-to-disk#in-a-browser).

Before trusting a browser certificate warning, compare its SHA-256 fingerprint with this file read at the machine's own console:

```sh
cat /var/state/gxwi/certificate.sha256
```

Do not enter credentials if the fingerprints differ. See [the machine's certificate](~peios/signing-in-from-a-browser/the-certificate) for verification and browser-trust details.

1. Choose the installation operation.
2. Select the internal disk by its **device, model, size, and bus**. The USB medium is marked and cannot be selected.
3. Review the erasure confirmation, including the existing systems and used filesystems it found. Go back if anything is unexpected. An unrecognised or encrypted filesystem may not have its contents listed; it will still be erased.
4. Confirm the install. In the browser, hold down the button that starts it.
5. Leave the machine and medium connected until the installer reports **Installation complete. Reboot to start Peios.** Closing a surface does not cancel the daemon's installation.

[Installing to disk](~peios/disks-and-filesystems/installing-to-disk) explains progress, failures, the disk layout, and the older command-line script.

## Restart from the installed disk

After the installation-complete message, remove the USB stick **before** choosing **Reboot now**. Do not remove it while installation is still running.

The installer does not change firmware boot order. If the machine returns to the installer, it probably booted from the stick again: remove the stick and restart. You do not need to install again.

Once disk boot is working, you can put the internal disk first in firmware boot order. Remove obsolete boot entries only after identifying them as entries for the system you replaced.

## First boot

[First-boot setup](~peios/disks-and-filesystems/first-boot-setup) creates your administrator account, sets the machine's name, and optionally applies a manual wired-network address. It is available on the console and, when the image includes it, at the browser address.

`installerd` attempts to carry the live medium's GXWI key and certificate into
the installed system. The transfer can be skipped or fail without failing the
installation, so the completion message does not prove that the certificate is
unchanged. If the installed fingerprint differs, verify it through the
installed machine's trusted console before entering credentials. See
[certificate carry-over and first boot](~peios/signing-in-from-a-browser/the-certificate#installation-and-first-boot).
Automatic waiting and reconnecting also depend on browser trust; if the tab
shows a browser error after restart, reopen the address manually.

> [!NOTE]
> **Peios 2026.8:** after assigning a new address to the interface your browser uses, the setup page may stay on its starfield rather than follow the machine over HTTPS. Once setup finishes, open `https://<new-address>:7780` yourself. The browser can warn again at the new address; compare the certificate with the fingerprint you verified. The general first-boot guide describes automatic reconnection, so keep this release-specific workaround in mind.

Check the result:

- The PC starts from its internal disk with the USB stick removed.
- Setup finishes and gives you a sign-in prompt.
- You can sign in with the account and password you just created.
- If you changed the network address, the new address reaches the sign-in page.

If setup repeatedly fails, keep the install medium available and follow [first-boot recovery](~peios/disks-and-filesystems/first-boot-setup#it-runs-once).

## Machines known to work

| Machine | Documented result |
|---|---|
| Beelink Mini S (Intel Alder Lake-N) | Ethernet (`r8169`), NVMe, and USB work without configuration. Intel Wi-Fi is detected, but joining a wireless network is not yet available. |
