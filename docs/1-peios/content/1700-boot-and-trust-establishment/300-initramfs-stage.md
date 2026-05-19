---
title: The initramfs stage
type: concept
description: Between the kernel finishing its own initialisation and peinit taking over on the real root, Peios runs a small in-memory userspace stage — the initramfs — with prelude as its PID 1. prelude prepares the environment, runs the hooks that mount the real root, and hands the machine off. This page covers what the initramfs stage is for, the prelude component, the /system/boot/prelude/ directory the initramfs is built from, how it is kept current, and the handoff to the real root.
related:
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/bootstrap-tokens
  - peios/boot-and-trust-establishment/boot-hooks
  - peios/boot-and-trust-establishment/peinit-pid-1
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

The initramfs is not a mysterious binary blob. It is **compiled from an ordinary directory** on the real root filesystem: `/system/boot/prelude/`. Whatever is in that directory becomes the contents of the in-memory root. The directory is the source; the initramfs image is the build product.

The layout is straightforward:

```
/system/boot/prelude/
    init             the prelude binary — becomes the initramfs PID 1
    bin/
        busybox      supplies /bin/sh and the utilities hooks call
    hooks/
        mount-root.sh    the boot hooks
        ...
```

It is a normal directory. You can list it, read it, and see exactly what the initramfs will contain — inspecting the boot environment is `ls /system/boot/prelude/`, not unpacking an archive. This is intentional: the initramfs should feel like part of the filesystem an administrator already understands, not a separate, opaque build system.

Most of what lands in the directory is put there by **packages**. A boot feature — disk encryption, an exotic storage backend — is an ordinary peipkg; installing it drops its hook (and any helper binaries) into `/system/boot/prelude/`, and removing the package takes them away. There is no separate "initramfs configuration" to edit and no central list of supported features: the directory *is* the configuration, and a package contributes to the boot simply by installing files into it. [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks) covers this in full.

Because hooks are shell scripts, the initramfs has to carry a shell. `bin/busybox` is a single static binary that provides `/bin/sh` along with the standard utilities a hook invokes — `mount`, `modprobe`, `blkid`, and the rest.

## What prelude does at boot

When the kernel starts prelude, it runs one fixed sequence, in order:

1. **Prepare the environment.** prelude mounts the kernel's virtual filesystems — `/proc`, `/sys`, `/dev` — so that it and the hooks can see processes, devices, and kernel state, and arranges the mount environment so the later root switch is unobstructed.
2. **Determine the target init.** prelude reads the kernel command line for an `init=` value — the program to hand off to on the real root. If the command line does not name one, prelude falls back to a standard search (`/sbin/init`, `/etc/init`, `/bin/init`, and finally `/bin/sh`) on the real root once it is mounted.
3. **Run the hooks.** prelude creates an empty `/sysroot` directory — the mount point the real root will appear at — and runs the boot hooks in order. The hooks do the deployment-specific work: load drivers, unlock encryption, assemble volumes, and mount the real root onto `/sysroot`. prelude does none of this itself; it runs the hook list. The order was decided when the initramfs was built (see below, and [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks)).
4. **Verify the real root.** After the hooks have run, prelude checks that `/sysroot` actually has a filesystem mounted on it. If no hook mounted a root, prelude fails the boot rather than handing off to nothing. This is the one outcome prelude insists on: some hook must have produced a mounted root.
5. **Hand off.** prelude carries the kernel virtual filesystems into the new root, frees the now-finished in-memory root to reclaim its space, switches `/` to the real root, and executes the target init. From that exec onward, the initramfs is gone and the real system is running.

prelude runs this sequence exactly once. It does not loop, supervise, or stay resident — the moment the real init is exec'd, prelude has ceased to exist; the exec replaces it. Its entire lifetime is the few seconds of the initramfs stage.

## When the initramfs stage fails

prelude does not limp. If any step fails — a hook exits with an error, no hook mounts the root, the target init cannot be found — prelude **stops and halts the machine**. It does not fall through to a half-configured system, and it does not try to work around a failed hook.

This is the right behaviour for the stage. The initramfs's only job is to deliver a correctly-mounted real root to a real init. A failure there means the system cannot be brought up safely; continuing would only produce a system in an undefined state. Halting makes the failure unambiguous — the console shows which step failed — and leaves the operator with a clean situation to diagnose rather than a subtly-broken running system.

## Keeping the initramfs current

Because the directory is the source and the initramfs image is a build product, the two have to be kept in step. Whenever `/system/boot/prelude/` changes — a feature package is installed or removed, the kernel is updated, an administrator edits a hook — the image has to be rebuilt from the directory.

The tool that does this is **mkirf**. It reads `/system/boot/prelude/`, resolves the order the hooks must run in, checks the directory is internally consistent, and writes the compressed initramfs image. Three properties of it matter to an operator:

- **It validates.** mkirf will not produce an image from a directory that cannot boot. A hook set with an impossible ordering, a hook that depends on a capability nothing provides, a missing `init` — each of these stops the build with a clear error. A misconfigured boot is caught when the image is built, on a running system where the message is easy to read, rather than as a mystery failure at the next boot. [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks) covers exactly what is checked.
- **It is deterministic.** The same directory always compiles to the same image, byte for byte — identities, timestamps, and ordering are all normalised. This is what makes "did anything actually change?" a meaningful question, and it underpins later work such as signed boot artifacts.
- **It keeps the directory pristine.** mkirf reads the directory and writes the image elsewhere; it never writes back into `/system/boot/prelude/`. The resolved hook order is recorded *inside the image*, not in the source. The directory you inspect is always exactly what packages and you have put there.

mkirf can run once and exit, or run in a **watch mode** where it stays resident and recompiles automatically whenever the directory changes. Watch mode is what lets `/system/boot/prelude/` behave like an ordinary part of the filesystem — edit a hook and the initramfs is current again — rather than a build artifact an administrator has to remember to regenerate.

When more than one kernel is installed, there is one initramfs per kernel: the drivers a kernel needs are specific to its version, so each kernel gets an image built against its own modules.

## The handoff to the real root

The final act of the initramfs stage is the **handoff**: prelude replaces the in-memory root with the real root and gives the machine to the real init.

Concretely, the real root has been mounted at `/sysroot` by a hook; prelude carries the kernel virtual filesystems across into it, switches `/` from the initramfs to `/sysroot`, and `exec`s the target init. Switching the root is the operation usually called `switch_root` — after it, `/` is the real filesystem and the in-memory initramfs is gone, its RAM reclaimed.

The init prelude execs is the one identified back in step 2 — the `init=` value from the kernel command line, or the fallback search. On a complete Peios system that init is **peinit**, which takes over as PID 1 of the real root and brings up the rest of userspace. During earlier development, before peinit exists, the target is a simpler stand-in; the contract is the same either way — prelude delivers a mounted real root and a console, and execs whatever the real init is.

The handoff is a one-way door. Once `/` is the real root and the real init is running, the initramfs is not coming back; the in-memory stage exists only up to this moment. The SYSTEM token, though, **survives the handoff** — the real init inherits it across the exec, exactly as every program inherits its primary token across exec. That is the thread tying this page to [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens): the SYSTEM token the kernel attached to prelude is the same token peinit starts life holding.

## What prelude does not do

A few clarifications:

- **prelude does not mount the real root itself.** A hook does. prelude provides the `/sysroot` mount point and verifies the result, but the mount is always a hook's job — that is what keeps prelude identical across deployments. See [Boot hooks](~peios/boot-and-trust-establishment/boot-hooks).
- **prelude does not decide hook order.** The order is resolved when the initramfs is built, by mkirf, and recorded in the image. prelude reads the resolved list and runs it; it has no ordering logic of its own.
- **prelude does not supervise anything.** It runs the hook sequence once and execs the real init. It has no steady state — contrast peinit, which runs as the system's lifecycle manager for the whole of its uptime.
- **prelude is not the real init.** It is the initramfs init. peinit is the real-root init. They are separate binaries with separate jobs; prelude's last act is to exec the real init, not to become it.
- **prelude does not persist anything.** Nothing it does is written to disk. The initramfs is in RAM, used once, and discarded. Persistent state begins on the real root, with peinit.
