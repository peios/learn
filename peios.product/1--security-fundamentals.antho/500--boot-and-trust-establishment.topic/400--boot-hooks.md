---
title: Boot hooks
type: concept
description: Boot hooks do the deployment-specific work of early boot. Where they live, the metadata block, the four ordering keys, and the exit-code protocol.
related:
  - peios/boot-and-trust-establishment/initramfs-stage
  - peios/boot-and-trust-establishment/overview
  - peios/boot-and-trust-establishment/peinit-pid-1
---

A **boot hook** is a shell script that runs inside the initramfs, before the real root is mounted — during the [initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage). Hooks are how Peios keeps prelude deployment-agnostic: every part of early boot that depends on *this particular machine* is a hook, and prelude runs the hooks without knowing what any of them do.

The work hooks do is the work of getting to the real root: loading the storage driver that makes the system's disk visible; unlocking an encrypted container; assembling an LVM volume group or a RAID array; and, finally, mounting the real root filesystem onto `/mnt/rootfs`. None of that is the same on two arbitrary machines, so none of it is built into prelude — it is all hooks. prelude supplies the fixed skeleton of the boot; hooks supply everything that varies.

## Where hooks live

Hooks live in two directories, which mirror the layout's vendor/operator split everywhere else:

| Directory | For |
|---|---|
| `/usr/libexec/prelude/hooks.d/` | hooks shipped by packages |
| `/lcl/libexec/prelude/hooks.d/` | hooks an operator put there by hand |

Every regular file directly in either directory is a hook, and prelude runs all of them. Neither is searched recursively — a subdirectory is not a hook — and the file extension does not matter. A hook is recognised by being a file in one of those directories, and it is run according to its `#!` shebang line, the same way any script is run.

**A file name identifies a hook.** The same name in both directories is one hook with two candidate bodies, not two hooks: the operator's copy wins and the packaged one is skipped, so a shipped hook can be replaced without deleting a package's payload. The build says which file lost, because a hook silently replaced by another is exactly the kind of thing that should not be quiet.

An older `hooks/` directory at the initramfs root is still read, and every hook found there produces a build warning naming where it should move. That is deliberate: a hook in a directory nobody scans is not an error — it simply is not there, and the boot fails much later with nothing mounted — so the move cannot be a flag day. The warning going quiet is what says the migration is done. Hooks are `#!/usr/bin/sh` scripts, and the initramfs's `/usr/bin/sh` is provided by dash. The full package-storage path is required because hooks run before a `/bin` runtime view exists.

## How hooks get there

There are two ways a hook reaches the directory, and they are identical as far as prelude is concerned:

- **From a package.** Most hooks arrive as part of a feature peipkg. Installing `peios-luks` (disk encryption) drops a hook that unlocks encrypted volumes; installing a filesystem feature drops a hook that mounts that kind of root. The package's payload simply includes a file under `/usr/libexec/prelude/hooks.d/`, and removing the package removes the hook. This is the feature-as-a-package model applied to boot: there is no edition of Peios that "has LUKS" and another that does not — there is a `peios-luks` package, and a machine either has it installed or it does not.
- **By hand.** An administrator can write a hook and place it in `/lcl/libexec/prelude/hooks.d/` directly. A site with an unusual storage arrangement, or a one-off need, does not have to build a package — a script in the directory is a hook.

Either way, the next time the initramfs is built the new hook is picked up. (See [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage) for the build.)

## The ordering problem

Hooks have an order, and the order matters. A hook that mounts the root cannot run before the hook that loads the disk's storage driver; a hook that unlocks an encrypted volume cannot run before that volume's driver is loaded. Run them in the wrong order and the boot fails.

The obvious approach — number the files, `10-modules`, `20-crypto`, `30-mount`, and run them in numeric order — is the approach Peios deliberately does not take. Numeric prefixes work right up until two packages, written by people who never spoke to each other, both pick `20`. Then every package author has to know the whole number line, and the "order" is a fiction held together by convention. This is the historical sysvinit problem, and it does not scale.

Instead, a hook declares **what it needs and what it offers**, in terms of named *capabilities*, and the order is computed from those declarations. The hook that mounts the root says "I require `crypto-unlocked`"; the hook that unlocks encryption says "I provide `crypto-unlocked`"; the order follows. No hook needs to know any other hook's name or position — only the capabilities. Packages that never met each other compose correctly because they agree on capability names, not on numbers.

## The metadata block

A hook declares its capabilities in a **metadata block** at the top of the script: a fenced comment block, every line of it a comment, so the block is invisible to the shell when the script actually runs.

```sh
#!/usr/bin/sh
# /// hook
# contributes = ["rootfs-ready"]
# ///

# ... the hook's actual work follows ...
cryptsetup open /dev/sda2 root
```

The rules of the block are small and exact:

- It **opens** with a line that is exactly `# /// hook` and **closes** with a line that is exactly `# ///`.
- Every line in between is a **comment line** — `# ` followed by content, or a bare `#`. This is what keeps the block inert: the shell sees only comments.
- The content of those lines, with the `# ` stripped, is up to four keys:
  - `provides` — capabilities this hook satisfies **on its own**. Several hooks may provide the same capability, and any one of them suffices; they are alternatives.
  - `contributes` — capabilities this hook is **one part of**. Every contributor must complete before the capability counts as satisfied.
  - `requires` — capabilities that must already be satisfied before this hook runs. If nothing supplies one, the build fails.
  - `after` — capabilities to be ordered after **if anything supplies them**. If nothing does, the hook simply runs; this is not an error.
- Each key's value is a list of capability names in double quotes — `provides = ["a", "b"]`. An empty list is allowed, and a trailing comma is allowed.

### Why there are four keys and not two

The four are two ways to *supply* a capability crossed with two ways to *consume* one, and each pair exists to say something the other cannot.

**`contributes` is how a hook runs *before* something.** A hook is otherwise ordered only by what it consumes — so "run before the root is mounted" would require the root-mounting hooks to name your hook, which they cannot, because they were packaged before it existed. Declaring yourself part of a capability inverts the relationship: everything that consumes it now waits for you. Without this, the only way to be early is to win the file-name tie-break, which is the numeric-prefix problem wearing a disguise.

**`after` is how a shared vocabulary survives a small image.** A `requires` on a capability nothing supplies is a build error — deliberately, since it catches an initramfs that cannot possibly boot. But that makes any *standard* capability name dangerous: a hook mentioning `network-up` would break every image that has no networking. `after` expresses "if this happens at all, it happens before me", which is what most ordering against an optional milestone actually means.

**`provides` and `contributes` differ in what "satisfied" means.** With alternatives, one supplier doing the job is enough — which is exactly the live-boot/disk-boot pair below, where one mounts the root and the other stands aside. With contributors, the capability is not satisfied until every one of them has completed — three hooks each unlocking a layer of an encrypted stack, say. A capability must be one or the other; declaring it both ways is a build error, because there would be no answer to whether it is satisfied yet.

The format is a small, deliberate subset of TOML: enough to declare two lists of names, and no more. It is checked **strictly** when the initramfs is built — an unknown key, a list that is not well-formed, a block that is opened and never closed, two blocks in one file — each of these is a build error, not a quiet misread. A typo in a hook's metadata is caught at build time, with a message naming the hook and the line.

The metadata lives *inside* the hook script, not in a separate file, so a hook is a single self-contained thing: copy the script and its ordering travels with it.

## The capability vocabulary

Capabilities are just names, and a hook can in principle name its own. But the milestones every initramfs passes through are a small fixed vocabulary, so that hooks from unrelated packages line up against the same reference points:

| Capability | Meaning |
|---|---|
| `initramfs-ready` | The initramfs itself is usable — its filesystem topology assembled, its console set up. |
| `rootfs-ready` | `/mnt/rootfs` is mounted and ready for read/write manipulation. |
| `rootfs-strata-ready` | The full StrataFS topology exists *inside* `/mnt/rootfs`. |

The vocabulary is deliberately short. Names for things Peios does not yet do — driver loading, device settling, volume assembly — are not reserved in advance: a capability that nothing supplies and nothing consumes is a name with no meaning behind it, and inventing one early only fixes a shape before we know it.

Once every hook has finished, prelude chroots into `/mnt/rootfs`. There is no "last point at which a hook can run" capability, because that is already every hook's guarantee.

### `initramfs-ready` is the one capability with a rule

A hook that must run **before all the others** cannot say so by ordinary means — it would need every other hook to name it, including hooks written by people who have never heard of it, whose forgetting would not fail the build but would quietly run their hook in an initramfs with no `/bin`.

So `initramfs-ready` carries one extra rule:

> **Every hook that does not supply `initramfs-ready` is implicitly ordered after it.**

The exemption is *derived*, not declared — you are exempt exactly when you are part of the capability. There is no cycle to construct and nothing for a hook author to remember. A hook assembling the initramfs's own topology simply declares `contributes = ["initramfs-ready"]` and lands before everything.

Two things fall out of the existing rules rather than needing special cases. An initramfs with **no** contributors leaves the capability unsupplied, and an `after` on an unsupplied capability is vacuous — so a minimal initramfs just runs, with nothing to configure. And a hook carrying **no metadata block** does not gain the edge, because it already runs after every declaring hook; adding it would have pulled the escape hatch into the DAG.

mkirf materialises these edges into the sequence as ordinary `after` entries, rather than leaving prelude to know the rule. That keeps one implementation instead of two that have to agree, and makes the sequence file explain itself — in a rescue shell you can read why a hook ran where it did, instead of needing a rule that appears nowhere in the image.

### More than one hook may supply the same capability

Nothing limits a capability to a single supplier, and `rootfs-ready` is where that matters: getting a root filesystem ready is several jobs. A hook that unlocks an encrypted container, a hook that assembles a volume group, and a hook that performs the mount each `contributes = ["rootfs-ready"]`, and the capability is not achieved until all of them have finished. None of them needs to know the others exist.

A capability does not have to be a hard, machine-specific thing. What matters for ordering is the *declaration*, not how much work the hook does to honour it. An encryption hook on a machine with no encrypted volumes has nothing to unlock and **declines** (exit `69`) — which, for a capability it contributes to, completes its part: "nothing needed doing here" is a way of being done. The capability is still achieved, and everything waiting on it proceeds.


## How the order is resolved

When the initramfs is built, mkirf reads every hook's metadata and computes the running order:

- A hook that **consumes** a capability (by `requires` or by `after`) runs after **every** hook that **supplies** it (by `provides` or by `contributes`). That single rule is the whole of the ordering.
- Hooks with no ordering relationship between them run in a stable, predictable order — by file name — so the resolved sequence is the same every time the initramfs is built.

Note that ordering does not distinguish alternatives from contributors, nor hard requirements from soft ones: all four keys produce the same "supplier first" edge. What they change is *validity* — whether an unsupplied capability is an error — and what a capability being "satisfied" will mean to prelude at boot.

Three situations are build errors. They stop the build, and no initramfs is produced:

- A **cycle** — hook A consumes something B supplies, and B consumes something A supplies. There is no order that satisfies both; the build reports the hooks caught in the cycle.
- An **unsatisfied requirement** — a hook `requires` a capability that *nothing* installed supplies. Rather than build an initramfs that is guaranteed to fail at boot, mkirf reports the missing capability. An `after` on an unsupplied capability is explicitly fine.
- A **capability that is both provided and contributed to** — one hook calls it an alternative, another calls itself a part of it. The two answers to "is it satisfied?" contradict each other, so mkirf names both sides and stops rather than picking one.

This is the payoff of declared capabilities: an impossible or incomplete hook set is a build error on a running system, with a readable message, never a boot that hangs with no explanation.

The resolved order is recorded inside the initramfs image, at `/system/prelude/hooks.seq.<n>`, and prelude reads it at boot. An operator does not write or edit those files — they are generated. The hook directories are the source of truth; the order is derived from what they contain.

The `<n>` is the format version, and mkirf writes every version it can express faithfully, prelude reading the newest it understands. That is not ceremony: mkirf ships in `peiosutils` and prelude in its own package, so an image can pair a newer writer with an older reader, and separate files are what let one image satisfy both. A sequence newer than prelude understands is a warning when a usable one sits beside it, and a boot failure when it is the only one present.

A **missing** sequence is always an error, never "no hooks to run" — mkirf writes one for every image, including an empty one for an image with no hooks at all. Were an absent file read as "nothing to do", a manifest that failed to generate would become a boot that silently ran no hooks, mounted no root, and reported the failure a long way from its cause.

## Hooks with no metadata

A hook is allowed to carry no metadata block at all. It is still a valid hook — it simply has no declared capabilities, and therefore no ordering constraints. Such a hook runs **after** all the hooks that do have constraints, in file-name order.

The build emits a **warning** for a hook with no block — because a hook that merely forgot its metadata looks identical to one that genuinely has none, and the warning makes the difference visible. A hook that is *deliberately* unconstrained can carry an empty block — a `# /// hook` line immediately followed by `# ///` — to say so on purpose, which suppresses the warning.

## How prelude runs a hook

At boot, prelude runs the hooks one at a time, each to completion before the next begins, scheduling from their declarations — repeated passes over the sequence, running whatever is ready, retrying anything that deferred once something else has progressed. Each hook runs as a separate process with a minimal environment — `PATH=/usr/bin` and `TERM=linux` — so the initramfs's shell and utilities (dash, peiosutils, and any tools a feature package added) are found without depending on a not-yet-mounted root-level view.

A hook reports what happened through its **exit code**, and there are four things it can say:

| Exit | Meaning | What prelude does |
|---|---|---|
| `0` | **Satisfied** — I did my part. | Its `provides` are achieved; its `contributes` are one step closer to complete. |
| `69` | **Declined** — not applicable on this machine. | It is not counted toward the capabilities it declared. |
| `75` | **Deferred** — I cannot run yet, and I have changed nothing. | Re-queued and tried again once something else has made progress. |
| anything else | **Failed.** | The boot stops and the machine halts. |

The two middle codes are borrowed from `sysexits.h` (`EX_UNAVAILABLE`, `EX_TEMPFAIL`) rather than invented, for a practical reason: `1` and `2` are what any failing command returns and `126`, `127` and `128+n` are the shell's own, so a small dedicated range is the only place a deliberate signal cannot be mistaken for an accident. A hook killed by a signal is always a failure, whatever code it might have produced.

### Declining is not the same as succeeding

A hook that is not the right one for this machine **declines** (`69`) rather than exiting `0`. The difference matters because `provides` means *alternatives*: a capability with several providers is achieved as soon as one of them is satisfied, and a provider that exits `0` is claiming to be that one.

This is what the live-boot/disk-boot pair does. Whichever hook `root=` does not select declines, and the other mounts the root. If **every** provider declines, the capability is never achieved and prelude stops with a message naming it — where previously a machine no hook would boot produced only the generic "nothing mounted the root" much later.

For `contributes` the sense is reversed: since every contributor must complete, a contributor that declines has completed — "nothing needed doing here" is a way of being done.

### Deferring is a promise that nothing happened

**Deferred** (`75`) means the hook's inputs are not ready yet. prelude runs hooks in repeated passes, retrying deferred ones once something else has progressed, and stops with a diagnosis if a whole pass completes nothing while work remains.

The contract that makes this safe is that a deferring hook has **done nothing**. Re-running it is free in a way that re-running a *failed* hook could never be — a failure may have left a half-assembled array, an opened device, or a burnt unlock attempt behind it. So:

- **Defer before you act, never after.** Check whether you can do the job; if not, exit `75` immediately. Do not defer partway through.
- **Failure is still failure.** If the work was attempted and went wrong, exit non-zero. Deferring a genuine error turns one clear failure into a stall reported as "nothing left to wait for".

This is what lets layered arrangements compose without absolute ordering: three hooks each contributing to an encrypted stack can be written without knowing which layer comes first, because the ones whose devices do not exist yet simply defer and are retried.

A few more consequences for anyone writing a hook:

- **Check, and exit non-zero on failure.** A hook that mounts the root must exit non-zero if the mount failed. A hook that fails silently turns into prelude's generic "nothing mounted the root" failure later — which is harder to diagnose than the hook reporting its own error at the point it happened.
- **Hooks run as SYSTEM.** Everything in the initramfs runs on the SYSTEM token (see [Bootstrap tokens](~peios/boot-and-trust-establishment/bootstrap-tokens)), so a hook has full authority. There is no identity model to work within inside the initramfs — that begins on the real root.

## Writing a hook

A complete, minimal hook — one that mounts an ext4 root from a known partition:

```sh
#!/usr/bin/sh
# /// hook
# contributes = ["rootfs-ready"]
# ///

# The device may not exist yet — another hook may still have to unlock or
# assemble it. Defer rather than fail: exit 75 promises we changed nothing,
# so prelude can retry us once something else has made progress.
[ -b /dev/mapper/root ] || exit 75

mount -t ext4 /dev/mapper/root /mnt/rootfs || exit 1
```

What this declares: it is one part of `rootfs-ready`, so anything waiting on a usable root filesystem is ordered after it. It does not name the hooks it depends on, because it does not know them.

A hook that unlocks the container it mounts, to pair with it:

```sh
#!/usr/bin/sh
# /// hook
# contributes = ["rootfs-ready"]
# ///

# Nothing encrypted on this machine — decline, which completes our part of
# the conjunction without claiming to have unlocked anything.
[ -e /dev/sda2 ] || exit 69

cryptsetup open /dev/sda2 root || exit 1
```

Installed together, these two compose without either one naming the other, and **without an ordering declaration between them at all**. If the mount hook runs first it finds no device and defers; the unlock hook then runs; the mount hook is retried and succeeds. Add a volume-assembly hook later — also just `contributes = ["rootfs-ready"]` — and it slots in the same way, because each hook knows only whether *it* can act yet.

That is the model: hooks are composed by capability, ordering is declared only where it is genuinely known, and the rest is settled at boot by hooks that can say "not yet".

## What hooks are not

A few clarifications:

- **Hooks do not run on the real root.** They run inside the initramfs, before the handoff. Work that belongs to the running system — starting services, applying mount and access policy — is [peinit](~peios/boot-and-trust-establishment/peinit-pid-1)'s job, not a hook's.
- **A boot hook is not a service.** "Hook" here means specifically an initramfs hook. The initramfs stage ends when prelude execs the real init; everything after that — services, supervision, restart policy — is peinit's domain and works nothing like a hook.
- **The generated order file is not edited by hand.** It is the build's record of the resolved order. The `hooks/` directory is the source; the order is computed from it, every time the image is built.
- **File names are not the ordering mechanism.** A file name identifies a hook, and is the tie-break between hooks that have no capability relationship. Renaming a hook does not change where it runs relative to a hook it shares a capability with — the `provides`/`requires` declarations do that.

## Where to go next

For the stage that runs the hooks, read [The initramfs stage](~peios/boot-and-trust-establishment/initramfs-stage).

For the build that validates hooks and resolves their order, read [mkirf](~peios/boot-and-trust-establishment/mkirf).

For what takes over once a hook has mounted the real root, read [peinit at PID 1](~peios/boot-and-trust-establishment/peinit-pid-1).
