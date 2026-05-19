---
title: Boot hooks
type: concept
description: A boot hook is a shell script the initramfs runs before the real root is mounted. Hooks do every deployment-specific part of early boot — loading drivers, unlocking encryption, assembling volumes, mounting the real root. Each hook declares the capabilities it provides and requires, and the build resolves a safe running order from those declarations. This page covers where hooks live, the metadata format, the capability vocabulary, how ordering and failures behave, and how to write one.
related:
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/peinit-pid-1
---

A **boot hook** is a shell script that runs inside the initramfs, before the real root is mounted — during the [initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage). Hooks are how Peios keeps prelude deployment-agnostic: every part of early boot that depends on *this particular machine* is a hook, and prelude runs the hooks without knowing what any of them do.

The work hooks do is the work of getting to the real root: loading the storage driver that makes the system's disk visible; unlocking an encrypted container; assembling an LVM volume group or a RAID array; and, finally, mounting the real root filesystem onto `/sysroot`. None of that is the same on two arbitrary machines, so none of it is built into prelude — it is all hooks. prelude supplies the fixed skeleton of the boot; hooks supply everything that varies.

## Where hooks live

Hooks are files in `/system/boot/prelude/hooks/`. Every regular file directly in that directory is a hook, and prelude runs all of them. The directory is not searched recursively — a subdirectory is not a hook — and the file extension does not matter. A hook is recognised by being a file in `hooks/`, and it is run according to its `#!` shebang line, the same way any script is run. In practice hooks are `#!/bin/sh` scripts, and the initramfs's `/bin/sh` is the one provided by busybox.

## How hooks get there

There are two ways a hook reaches the directory, and they are identical as far as prelude is concerned:

- **From a package.** Most hooks arrive as part of a feature peipkg. Installing `peios-luks` (disk encryption) drops a hook that unlocks encrypted volumes; installing a filesystem feature drops a hook that mounts that kind of root. The package's payload simply includes a file under `/system/boot/prelude/hooks/`, and removing the package removes the hook. This is the feature-as-a-package model applied to boot: there is no edition of Peios that "has LUKS" and another that does not — there is a `peios-luks` package, and a machine either has it installed or it does not.
- **By hand.** An administrator can write a hook and place it in `hooks/` directly. A site with an unusual storage arrangement, or a one-off need, does not have to build a package — a script in the directory is a hook.

Either way, the next time the initramfs is built the new hook is picked up. (See [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage) for the build.)

## The ordering problem

Hooks have an order, and the order matters. A hook that mounts the root cannot run before the hook that loads the disk's storage driver; a hook that unlocks an encrypted volume cannot run before that volume's driver is loaded. Run them in the wrong order and the boot fails.

The obvious approach — number the files, `10-modules`, `20-crypto`, `30-mount`, and run them in numeric order — is the approach Peios deliberately does **not** take. Numeric prefixes work right up until two packages, written by people who never spoke to each other, both pick `20`. Then every package author has to know the whole number line, and the "order" is a fiction held together by convention. This is the historical sysvinit problem, and it does not scale.

Instead, a hook declares **what it needs and what it offers**, in terms of named *capabilities*, and the order is computed from those declarations. The hook that mounts the root says "I require `crypto-unlocked`"; the hook that unlocks encryption says "I provide `crypto-unlocked`"; the order follows. No hook needs to know any other hook's name or position — only the capabilities. Packages that never met each other compose correctly because they agree on capability names, not on numbers.

## The metadata block

A hook declares its capabilities in a **metadata block** at the top of the script: a fenced comment block, every line of it a comment, so the block is invisible to the shell when the script actually runs.

```sh
#!/bin/sh
# /// hook
# provides = ["crypto-unlocked"]
# requires = ["modules-loaded"]
# ///

# ... the hook's actual work follows ...
cryptsetup open /dev/sda2 root
```

The rules of the block are small and exact:

- It **opens** with a line that is exactly `# /// hook` and **closes** with a line that is exactly `# ///`.
- Every line in between is a **comment line** — `# ` followed by content, or a bare `#`. This is what keeps the block inert: the shell sees only comments.
- The content of those lines, with the `# ` stripped, is up to two keys:
  - `provides` — the capabilities this hook satisfies once it has run successfully.
  - `requires` — the capabilities that must already be satisfied before this hook runs.
- Each key's value is a list of capability names in double quotes — `provides = ["a", "b"]`. An empty list is allowed, and a trailing comma is allowed.

The format is a small, deliberate subset of TOML: enough to declare two lists of names, and no more. It is checked **strictly** when the initramfs is built — an unknown key, a list that is not well-formed, a block that is opened and never closed, two blocks in one file — each of these is a build error, not a quiet misread. A typo in a hook's metadata is caught at build time, with a message naming the hook and the line.

The metadata lives *inside* the hook script, not in a separate file, so a hook is a single self-contained thing: copy the script and its ordering travels with it.

## The capability vocabulary

Capabilities are just names, and a hook can in principle name its own. But the common ones — the milestones every initramfs passes through — are a small fixed vocabulary, so that hooks from unrelated packages line up against the same reference points:

| Capability | Meaning |
|---|---|
| `modules-loaded` | The kernel modules the initramfs needs are loaded. |
| `udev-settled` | Device nodes exist for the hardware that is present. |
| `crypto-unlocked` | Encrypted block devices have been opened. |
| `volumes-activated` | Logical volumes and RAID arrays have been assembled. |
| `root-mounted` | The real root filesystem is mounted at `/sysroot`. |
| `pre-switch-root` | The last point at which a hook can run inside the initramfs. |

`root-mounted` is the most important of these, because it is the one prelude itself depends on. After the hooks have run, prelude checks that something is mounted at `/sysroot`; the hook that mounts the root is the hook that provides `root-mounted`. Every Peios initramfs has exactly such a hook — whether the root is a plain disk partition, an encrypted volume, or something more elaborate is the difference between one `root-mounted` hook and another.

A hook that needs to do work *after* the root is mounted but *before* the handoff — a last-minute fixup — requires `pre-switch-root`.

A capability does not have to be a hard, machine-specific thing. A hook may provide a capability trivially: the encryption hook on a machine with no encrypted volumes still provides `crypto-unlocked`, it simply provides it by doing nothing. What matters for ordering is the *declaration*, not how much work the hook does to honour it.

## How the order is resolved

When the initramfs is built, mkirf reads every hook's metadata and computes the running order:

- A hook that **requires** a capability runs after **every** hook that **provides** it. That single rule is the whole of the ordering.
- Hooks with no ordering relationship between them run in a stable, predictable order — by file name — so the resolved sequence is the same every time the initramfs is built.

Two situations are build errors. They stop the build, and no initramfs is produced:

- A **cycle** — hook A requires something B provides, and B requires something A provides. There is no order that satisfies both; the build reports the hooks caught in the cycle.
- An **unsatisfied requirement** — a hook requires a capability that *no* installed hook provides. Rather than build an initramfs that is guaranteed to fail at boot, mkirf reports the missing capability.

This is the payoff of declared capabilities: an impossible or incomplete hook set is a build error on a running system, with a readable message, never a boot that hangs with no explanation.

The resolved order is recorded inside the initramfs image, in a file prelude reads at boot. An operator does not write or edit that file — it is generated. The hooks in `/system/boot/prelude/hooks/` are the source of truth; the order is derived from them.

## Hooks with no metadata

A hook is allowed to carry no metadata block at all. It is still a valid hook — it simply has no declared capabilities, and therefore no ordering constraints. Such a hook runs **after** all the hooks that do have constraints, in file-name order.

The build emits a **warning** for a hook with no block — because a hook that merely forgot its metadata looks identical to one that genuinely has none, and the warning makes the difference visible. A hook that is *deliberately* unconstrained can carry an empty block — a `# /// hook` line immediately followed by `# ///` — to say so on purpose, which suppresses the warning.

## How prelude runs a hook

At boot, prelude runs the hooks one at a time, in the resolved order, each to completion before the next begins. Each hook runs as a separate process with a minimal environment — `PATH=/bin`, so the busybox utilities are found.

The contract for a hook is simple and strict: **exit zero on success, non-zero on failure.** A hook that exits non-zero **fails the boot** — prelude stops there and halts the machine (see [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage)). There is no "continue past a failed hook"; a hook that could not do its job means the boot cannot safely proceed.

A few consequences follow for anyone writing a hook:

- **Check, and exit non-zero on failure.** A hook that mounts the root must exit non-zero if the mount failed. A hook that fails silently turns into prelude's generic "nothing mounted the root" failure later — which is harder to diagnose than the hook reporting its own error at the point it happened.
- **A no-op is a success.** A hook whose work is not needed on this machine should do nothing and exit zero. It still provides its capability; it provides it trivially.
- **Hooks run as SYSTEM.** Everything in the initramfs runs on the SYSTEM token (see [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens)), so a hook has full authority. There is no identity model to work within inside the initramfs — that begins on the real root.

## Writing a hook

A complete, minimal hook — one that mounts an ext4 root from a known partition:

```sh
#!/bin/sh
# /// hook
# provides = ["root-mounted"]
# requires = ["modules-loaded"]
# ///

# Mount the real root read-only onto /sysroot, where prelude expects it.
mount -t ext4 -o ro /dev/sda2 /sysroot || exit 1
```

What this declares: it `requires` `modules-loaded`, so it runs after whatever loads the storage driver; it `provides` `root-mounted`, so prelude's post-hook check is satisfied and any hook that needs the root already mounted is ordered after it. The body does one thing, and exits non-zero if it fails.

A hook that loads a storage driver, to pair with it:

```sh
#!/bin/sh
# /// hook
# provides = ["modules-loaded"]
# ///

modprobe virtio_blk || exit 1
```

Installed together, these two compose without either one naming the other: the driver hook provides `modules-loaded`, the mount hook requires it, so the driver hook runs first. Add an encryption hook later — one that provides `crypto-unlocked` and requires `modules-loaded` — and change the mount hook to require `crypto-unlocked` instead, and all three fall into the right order automatically. That is the model: hooks are composed by capability, and the order takes care of itself.

## What hooks are not

A few clarifications:

- **Hooks do not run on the real root.** They run inside the initramfs, before the handoff. Work that belongs to the running system — starting services, applying mount and access policy — is [peinit](~peios/boot-and-trust-establishment/peinit-pid-1)'s job, not a hook's.
- **A boot hook is not a service.** "Hook" here means specifically an initramfs hook. The initramfs stage ends when prelude execs the real init; everything after that — services, supervision, restart policy — is peinit's domain and works nothing like a hook.
- **The generated order file is not edited by hand.** It is the build's record of the resolved order. The `hooks/` directory is the source; the order is computed from it, every time the image is built.
- **File names are not the ordering mechanism.** A file name is only the tie-break between hooks that have no capability relationship. Renaming a hook does not change where it runs relative to a hook it shares a capability with — the `provides`/`requires` declarations do that.
