---
title: The initramfs stage
type: concept
description: Between kernel init and peinit, prelude — the initramfs PID 1 — prepares the environment, runs the boot hooks that mount the real root, and hands off.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/boot-hooks
  - peios/boot-and-trust-establishment/peinit-pid-1
  - peios/boot-and-trust-establishment/mkirf
---

The kernel cannot reach the real root filesystem on its own. By the time it has finished its own initialisation it can speak to a CPU and some memory, but the disk the system is installed on may sit behind a storage driver that is not yet loaded, a volume manager that has not been assembled, or an encrypted container that has not been unlocked. Mounting that filesystem is work, and it is work that has to be done in userspace — the kernel does not mount real roots by guesswork.

So there is a stage in between. The bootloader loads a second thing into memory alongside the kernel: a small, complete root filesystem called the **initramfs**. The kernel unpacks it into a RAM-backed filesystem, makes that filesystem `/`, and starts a PID 1 inside it. This in-memory system exists for one purpose — to get the real root mounted and then get out of the way. On Peios, the PID 1 of that in-memory system is **prelude**.

The initramfs stage sits between two of the other pages in this topic. [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens) covers what the kernel constructs before any userspace exists; [peinit at PID 1](~peios/boot-and-trust-establishment/peinit-pid-1) covers the init system that runs on the real root. prelude is what runs in between — the first userspace process the system ever has, and the last thing that runs before the real system begins.

## prelude in the trust chain

prelude is the **first userspace process** on the machine. The kernel attaches the SYSTEM token to it — prelude is the "init" that [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens) describes the SYSTEM token being handed to. From the moment prelude starts, the "everything is SYSTEM" phase of boot (covered in the [overview](~peios/boot-and-trust-establishment/overview)) is underway: inside the initramfs there is exactly one identity, SYSTEM, and exactly one job, getting to the real root. There is no directory, no authd, no notion of separate principals — and no need for one. The initramfs is a single-purpose, single-identity environment.

The initramfs's integrity is the integrity of the **initramfs image itself**. The image is a sealed archive: once it is built, nothing edits it in place. It is read into RAM at boot, used once, and discarded at the handoff — there is nothing inside it to tamper with at runtime. Under Secure Boot (a later milestone), the firmware verifies the whole boot artifact — kernel and initramfs together — before the kernel is allowed to run at all, so the sealed image is also a *verified* one.

## prelude — the initramfs PID 1

prelude is a small, dedicated init. It is not a general-purpose process manager and it is not [peinit](~peios/boot-and-trust-establishment/peinit-pid-1): peinit supervises services for the system's entire lifetime, whereas prelude runs one short, fixed sequence and then replaces itself with the real init. They are separate programs with separate jobs. The name reflects the relationship — prelude is the short piece that runs before peinit's main one.

What prelude itself does is deliberately minimal. It is the **invariant skeleton** of the boot — the part that is identical on every Peios machine. Preparing the kernel's virtual filesystems, running the hooks, checking that a root was mounted, switching to it: that is the whole of prelude. Everything that *varies* between machines — which storage driver is needed, whether there is disk encryption, what kind of filesystem the root is — is not in prelude at all. It is in [boot hooks](~peios/boot-and-trust-establishment/boot-hooks).

This division is the important design point. A machine that boots from a plain disk, a machine that boots from an encrypted volume, and a machine that boots over a network differ only in their hooks. prelude is the same binary on all three. It never has to change to support a new kind of deployment — a new deployment is a new hook, not a new prelude.

## Where the initramfs comes from

The initramfs is not a mysterious binary blob. It is **compiled from an ordinary directory** on the real root filesystem: `/boot/initramfs/`. Whatever is in that directory becomes the contents of the in-memory root. The directory is the source; the initramfs image is the build product.

The layout is straightforward:

```
/boot/initramfs/
    init                 symlink to the prelude binary — the initramfs PID 1
    usr/
        sbin/prelude     the prelude binary itself
        bin/
            dash         the shell; sh -> dash provides /usr/bin/sh
            peiosutils   one multi-call binary backing mount, chroot, ls, … via symlinks
    lib64 -> usr/lib/x86_64-linux-peios
                         the x86-64 ABI loader path; /bin, /sbin and /lib views
                         do not exist before the runtime topology is mounted
    usr/libexec/prelude/hooks.d/
        mount-root.sh    mounts a live medium's squashfs (live-boot)
        mount-root-disk.sh
                         mounts an installed root partition (disk-boot); both
                         contribute rootfs-ready, and `root=` on the cmdline
                         decides which one acts
        mount-rootfs-stratafs-base.sh
                         mounts the real root's StrataFS views after rootfs-ready
        ...
    lcl/libexec/prelude/hooks.d/
                         operator-placed hooks; a file here replaces a packaged
                         hook of the same name
```

It is a normal directory. You can list it, read it, and see exactly what the initramfs will contain — inspecting the boot environment is `ls /boot/initramfs/`, not unpacking an archive. This is intentional: the initramfs should feel like part of the filesystem an administrator already understands, not a separate, opaque build system.

Most of what lands in the directory is put there by **packages**. A boot feature — disk encryption, an exotic storage backend — is an ordinary peipkg; installing it drops its hook (and any helper binaries) into `/boot/initramfs/`, and removing the package takes them away. There is no separate "initramfs configuration" to edit and no central list of supported features: the directory *is* the configuration, and a package contributes to the boot simply by installing files into it. [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks) covers this in full.

Because hooks are shell scripts, the initramfs has to carry a shell. That shell is **dash**: it provides the `sh` capability prelude depends on and supplies `/usr/bin/sh`. Hooks use `#!/usr/bin/sh`, because they run before any root-level `/bin` StrataFS view exists. The ordinary utilities a hook invokes — `mount`, `chroot`, `ls`, and the rest — come from **peiosutils**, a single multi-call binary that backs each tool through a symlink (`mount`, `chroot`, and friends are all the one binary, invoked under different names). Driver- or filesystem-specific tools a particular hook needs — `blkid`, a `mkfs` helper — arrive with the feature package that ships that hook, not with the base initramfs. Module loading is the exception: `modprobe` comes from **kmod** and the modules themselves from **kernel-modules-irf**, both base packages rather than per-feature ones, because any hook that touches storage may need them.

## Kernel modules in the initramfs

The initramfs carries its own set of kernel modules, shipped by the **kernel-modules-irf** package. It is a separate root from the real one and shares nothing with it, so it needs its own copy of anything it uses — the same reason it needs its own mountpoints and its own loader link.

The set is deliberately a **subset**. The initramfs only has to reach the root filesystem, so it carries storage controllers and block devices, the input drivers a passphrase prompt needs, filesystem and crypto drivers, and network drivers for a root reached over the network. It does not carry graphics, sound, media or wireless: the real root can load those for itself once it is mounted, and everything in the initramfs is paid for on every boot — it is loaded whole into memory, and under a [UKI](~peios/boot-and-trust-establishment/mkuki) it sits inside an image the firmware verifies in one piece.

The set is also **generic**: every machine gets the same modules, rather than a set tailored to the hardware it was built on. Two things make that the only workable choice. Composing a root resolves offline and runs no install-time side effects, so nothing in that path may inspect the hardware it is composing for. And because a UKI is signed as a single image, a per-machine initramfs would have to be assembled and signed on the target — which would mean a signing key on every installed machine. A generic initramfs is also what mainstream distributions default to; tailoring it is the opt-in, not the norm.

A module being *available* in the initramfs is not the same as it being loaded, and the kernel never loads a driver for hardware on its own: it enumerates the devices and emits a uevent for each one naming the module that can drive it, but binding a driver to a device is userspace's job. In the initramfs that job is done once, by the **coldplug hook** that the `coldplug-irf` package ships. It runs after the initramfs's own views are assembled and before any root-mount hook, reads the `modalias` of every device the kernel has enumerated under `/sys/bus`, and hands the whole set to `modprobe` in one call. A machine whose root sits behind a modular storage driver — NVMe, for instance — has that driver loaded by the time the root-mount hook goes looking for the disk. Aliases that match no module are the normal case and are ignored; a module that fails to load is reported and is not, on its own, a boot failure — whether the missing driver matters is for the root-mount hook to decide, because it is the one that knows which disk it needs.

The hook is a single pass and does not stay resident, which is enough for the initramfs: everything that matters to reaching the root is present before PID 1 runs. Devices that appear later, and the stable `/dev/disk/by-*` names, belong to the device manager on the real root.

## What prelude does at boot

When the kernel starts prelude, it runs one fixed sequence, in order:

1. **Prepare the environment.** prelude mounts the kernel's virtual filesystems — `/proc`, `/sys`, `/dev` — so that it and the hooks can see processes, devices, and kernel state, and arranges the mount environment so the later root switch is unobstructed.
2. **Determine the target init.** prelude reads the kernel command line for an `init=` value — the program to hand off to on the real root. The shipped image names `/bin/peinit2`. If the command line does not name one, prelude searches `/bin/peinit2`, `/sbin/init`, `/bin/init`, and finally `/bin/sh`. These are target-root runtime paths: the base-topology hook creates their StrataFS views before prelude hands off. Prelude's own initramfs rescue shell remains `/usr/bin/sh`, because that environment has no `/bin` view.
3. **Run the hooks.** prelude creates an empty `/mnt/rootfs` directory — the mount point the real root will appear at — and runs the boot hooks in order. The hooks do the deployment-specific work: load drivers, unlock encryption, assemble volumes, and mount the real root onto `/mnt/rootfs`. The packaged `mount-rootfs-stratafs-base.sh` hook (from the `fsbase` package) then mounts the conventional runtime views inside that root. prelude does none of this itself; it runs the hook list. The order was decided when the initramfs was built (see below, and [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks)).
4. **Verify the real root.** After the hooks have run, prelude checks that `/mnt/rootfs` actually has a filesystem mounted on it. If no hook mounted a root, prelude fails the boot rather than handing off to nothing. This is the one outcome prelude insists on: some hook must have produced a mounted root.
5. **Hand off.** prelude carries the kernel virtual filesystems into the new root, frees the now-finished in-memory root to reclaim its space, switches `/` to the real root, and executes the target init. From that exec onward, the initramfs is gone and the real system is running.

prelude runs this sequence exactly once. It does not loop, supervise, or stay resident — the moment the real init is exec'd, prelude has ceased to exist; the exec replaces it. Its entire lifetime is the few seconds of the initramfs stage.

## When the initramfs stage fails

prelude does not limp. If any step fails — a hook exits with an error, no hook mounts the root, the target init cannot be found — prelude **stops and halts the machine**. It does not fall through to a half-configured system, and it does not try to work around a failed hook.

This is the right behaviour for the stage. The initramfs's only job is to deliver a correctly-mounted real root to a real init. A failure there means the system cannot be brought up safely; continuing would only produce a system in an undefined state. Halting makes the failure unambiguous — the console shows which step failed — and leaves the operator with a clean situation to diagnose rather than a subtly-broken running system. The one way to intervene rather than halt is the debug knobs below.

## Debugging the initramfs stage

Two kernel command-line knobs (familiar from dracut) turn the fixed sequence into something an operator can step through. prelude reads them from `/proc/cmdline`, the same place it reads `init=` — as PID 1 it has no argv, so the command line is its only input. The interactive shell they open is dash, run as `sh -i` on the console.

- **`rd.shell`** — drop to a shell *on failure* instead of halting. If any boot step fails while `rd.shell` is set, prelude opens the shell so you can inspect the half-built initramfs: see what the hooks mounted, read the log, try a mount by hand. The failure still ends the boot — when you exit the shell, prelude halts as it would have anyway. Without `rd.shell`, a failure halts immediately.

- **`rd.break`** — stop *before any hook runs*. Bare `rd.break` pauses just before the first hook and opens the shell; exit the shell and the boot continues normally. This is the point where the kernel virtual filesystems are up but nothing deployment-specific has happened yet.

- **`rd.break=<hook>`** — stop just before a *named* hook. The value is matched against a hook's file name — or its full path — as it appears in the [resolved boot sequence](~peios/boot-and-trust-establishment/boot-hooks), so `rd.break=mount-root.sh` breaks immediately before that hook and lets everything ordered before it run first. The value is comma-separated and the flag may be repeated — `rd.break=modules.sh,mount-root.sh` — to break before several hooks.

The `rd.break` shells are true breakpoints, not failures: prelude forks them, so it stays PID 1 and the boot resumes exactly where it paused when the shell exits. Setting any `rd.break` also implies `rd.shell` — so if the boot goes on to fail, you get the failure shell too.

## Keeping the initramfs current

Because the directory is the source and the initramfs image is a build product, the two have to be kept in step. Whenever `/boot/initramfs/` changes — a feature package is installed or removed, the kernel is updated, an administrator edits a hook — the image has to be rebuilt from the directory.

The tool that does this is **mkirf** — see [mkirf](~peios/boot-and-trust-establishment/mkirf) for the full command reference. It reads `/boot/initramfs/`, resolves the order the hooks must run in, checks the directory is internally consistent, and writes the compressed initramfs image. Three properties of it matter to an operator:

- **It validates.** mkirf will not produce an image from a directory that cannot boot. A hook set with an impossible ordering, a hook that depends on a capability nothing provides, a missing `init` — each of these stops the build with a clear error. A misconfigured boot is caught when the image is built, on a running system where the message is easy to read, rather than as a mystery failure at the next boot. [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks) covers exactly what is checked.
- **It is deterministic.** The same directory always compiles to the same image, byte for byte — identities, timestamps, and ordering are all normalised. This is what makes "did anything actually change?" a meaningful question, and it underpins later work such as signed boot artifacts.
- **It keeps the directory pristine.** mkirf reads the directory and writes the image elsewhere; it never writes back into `/boot/initramfs/`. The resolved hook order is recorded *inside the image*, not in the source. The directory you inspect is always exactly what packages and you have put there.

mkirf can run once and exit, or run in a **watch mode** where it stays resident and recompiles automatically whenever the directory changes. Watch mode is what lets `/boot/initramfs/` behave like an ordinary part of the filesystem — edit a hook and the initramfs is current again — rather than a build artifact an administrator has to remember to regenerate.

When more than one kernel is installed, there is one initramfs per kernel: the drivers a kernel needs are specific to its version, so each kernel gets an image built against its own modules.

## The handoff to the real root

The final act of the initramfs stage is the **handoff**: prelude replaces the in-memory root with the real root and gives the machine to the real init.

Concretely, the real root has been mounted at `/mnt/rootfs` by a hook; prelude carries the kernel virtual filesystems across into it, switches `/` from the initramfs to `/mnt/rootfs`, and `exec`s the target init. Switching the root is the operation usually called `switch_root` — after it, `/` is the real filesystem and the in-memory initramfs is gone, its RAM reclaimed.

The init prelude execs is the one identified back in step 2 — the `init=` value from the kernel command line, or the fallback search. On a complete Peios system that init is **peinit**, which takes over as PID 1 of the real root and brings up the rest of userspace. During earlier development, before peinit exists, the target is a simpler stand-in; the contract is the same either way — prelude delivers a mounted real root and a console, and execs whatever the real init is.

The handoff is a one-way door. Once `/` is the real root and the real init is running, the initramfs is not coming back; the in-memory stage exists only up to this moment. The SYSTEM token, though, **survives the handoff** — the real init inherits it across the exec, exactly as every program inherits its primary token across exec. That is the thread tying this page to [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens): the SYSTEM token the kernel attached to prelude is the same token peinit starts life holding.

## What prelude does not do

A few clarifications:

- **prelude does not mount the real root itself.** A hook does. prelude provides the `/mnt/rootfs` mount point and verifies the result, but the mount is always a hook's job — that is what keeps prelude identical across deployments. See [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks).
- **prelude does not decide hook order.** The order is resolved when the initramfs is built, by mkirf, and recorded in the image. prelude reads the resolved list and runs it; it has no ordering logic of its own.
- **prelude does not supervise anything.** It runs the hook sequence once and execs the real init. It has no steady state — contrast peinit, which runs as the system's lifecycle manager for the whole of its uptime.
- **prelude is not the real init.** It is the initramfs init. peinit is the real-root init. They are separate binaries with separate jobs; prelude's last act is to exec the real init, not to become it.
- **prelude does not persist anything.** Nothing it does is written to disk. The initramfs is in RAM, used once, and discarded. Persistent state begins on the real root, with peinit.

## Where to go next

For the deployment-specific scripts prelude runs, read [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks).

For the init system prelude hands the machine to, read [peinit at PID 1](~peios/boot-and-trust-establishment/peinit-pid-1).

For the tool that compiles `/boot/initramfs/` into the image, read [mkirf](~peios/boot-and-trust-establishment/mkirf).
