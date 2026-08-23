---
title: StrataFS
type: reference
description: StrataFS merges ordinary directories by precedence while keeping each stratum independently manageable. Mounting a stack and the stratafs inspection tool.
related:
  - peios/disks-and-filesystems/overview
  - peios/mount-policies/mount
  - peios/file-access/overview
  - peios/boot-and-trust-establishment/boot-hooks
---

StrataFS presents several ordinary directories as one merged directory tree.
The directories remain ordinary and independently manageable at their real
paths; the StrataFS mount only supplies the merged view.

Strata are ordered from highest to lowest precedence. For each name, the first
stratum that holds it is its **provider**. Directories at the same name merge,
so their children are resolved in the same precedence order. A non-directory
provider masks every lower object at that name, including a lower directory's
whole subtree.

## A `/bin` example

Suppose `/usr/bin` contains packaged programs and `/lcl/bin` is for local
changes. Mount this stack at `/bin`:

```sh
mount -t stratafs none /bin -o 'strata=/lcl/bin+create:/usr/bin+ro'
```

`/lcl/bin` has higher precedence and receives newly-created objects. The `+ro`
on `/usr/bin` means “do not modify this stratum **through `/bin`**”. It does not
make the real `/usr/bin` mount read-only: an authorised writer can still modify
`/usr/bin/tool` directly at `/usr/bin/tool`.

Reading `/bin/tool` uses `/lcl/bin/tool` when it exists, otherwise
`/usr/bin/tool`. Writing an existing packaged tool through `/bin` copies it to
`/lcl/bin` first and changes the copy. Removing that copy through `/bin`
restores the unchanged `/usr/bin` version to view, because StrataFS does not use
whiteouts.

## The base Peios topology

The `fsbase` package installs the `mount-rootfs-stratafs-base.sh` [boot hook](~peios/boot-and-trust-establishment/boot-hooks)
in the initramfs. It runs after the deployment-specific hook has mounted the
real root and before prelude hands off to it, mounting the conventional
root-level views as one boot step:

| View | Strata, highest precedence first |
|---|---|
| `/bin` | `/lcl/bin+create`, `/usr/bin+ro+am` |
| `/sbin` | `/lcl/sbin+create`, `/usr/sbin+ro+am` |
| `/lib` | `/lcl/lib+create`, `/usr/lib+ro` |
| `/libexec` | `/lcl/libexec+create`, `/usr/libexec+ro+am` |
| `/share` | `/lcl/share+create`, `/usr/share+ro+am` |
| `/include` | `/lcl/include+create`, `/usr/include+ro+am` |
| `/etc` | `/system/retc`, `/lcl/etc+create`, `/usr/etc+ro+am` |
| `/conf` | `/lcl/conf+create`, `/usr/conf+ro+am` |

`am` permits an optional vendor directory to be absent when the system boots
and makes it participate automatically if a later package creates it. The
operator create directories are provisioned by `fsbase`; their absence is a
boot error rather than something StrataFS silently creates, because their own
security descriptors govern creation through each view.

`/lib` views `/usr/lib` rather than the architecture triplet directory beneath
it, so `/lib/modules` and `/lib/firmware` resolve. Both matter: kmod has
`/lib/modules` compiled in, and the kernel's firmware loader searches
`/lib/firmware`, and neither can be told to look elsewhere. Shared libraries are
unaffected — the loader finds them through its own absolute system search path
rather than through this view — and `/lib/x86_64-linux-peios/` still resolves,
one level down, which is the shape a foreign binary expects.

`/lib64` is not a StrataFS view. On x86-64 it remains the package-owned relative
symlink `lib64 -> usr/lib/x86_64-linux-peios`, because the psABI dynamic-loader
path must work before any hook can mount the base topology. It is a distinct
object from the `/lib` view above and is unaffected by what that view maps.

The mount option grammar is:

```text
strata=<stratum>[:<stratum>]...
<stratum> := <path>[+<flag>]...
<flag> := create | ro | am
```

Paths are absolute. `create` selects the one stratum that receives creations
and copy-up, `ro` prevents modification through the merged view, and `am`
allows the stratum directory itself to be temporarily absent. Literal `:`,
`+`, `,`, and `\` in a path are escaped with `\`.

## Inspecting a stack

The `stratafs` command is a read-only inspector. It does not mount, modify, or
clean anything, and it never gains extra authority. Every direct stratum read
runs with your normal access rights. If it cannot see all the information
needed for a complete answer—especially every participant of a protected
merged directory—it fails instead of showing a misleading partial result.

List every StrataFS mount in the current mount namespace, or one exact mount:

```sh
stratafs list
stratafs list /bin
```

Typical output is:

```text
/bin
  [0] /lcl/bin+create (present)
  [1] /usr/bin+ro (present)
```

The order is the precedence order. A stratum is `present`, `absent`, or
`not_directory`; the mount itself is also labelled when generically mounted
read-only.

## Explaining one path

Use `resolve` when you want to know why a name looks the way it does and where
a mutation would go:

```sh
stratafs resolve /bin/sh
```

The per-stratum states are:

| State | Meaning |
|---|---|
| `provider` | This object currently provides the name. |
| `participant` | This lower directory contributes to the merged directory. |
| `shadowed` | A higher object of the same type wins. |
| `masked` | A provider of another type hides this object. |
| `absent` | This stratum does not hold the path. |

The report also explains `write` and `delete`. A write can route `in_place`,
`copy_up`, or `create`; it can instead report `erofs`, a missing parent, an
unknown immutable-attribute state, or that content I/O follows a symlink.
Deletion identifies the real provider entry to remove and names a lower object
that will resurface. Removing a directory is still conditional on the complete
merged directory being empty.

These are routing answers, not authorisation promises. KACS checks the actual
operation against the caller when it is attempted.

For the kernel's answer without the explanation, print the synthetic origin
attribute:

```sh
stratafs origin /bin/sh
```

A non-directory prints its one real provider path. A merged directory prints
every participating real directory in precedence order, one escaped path per
line.

## Inspecting local state

The create stratum is deliberately easy to audit. `sweep` recursively reports
every object in it:

```sh
stratafs sweep /bin
```

Each result is classified as:

- `gap`: only the create stratum has this path;
- `override`: a lower stratum also has it; or
- `shadowed`: a higher stratum, or a higher non-directory ancestor, makes it
  unreachable.

Directories are included. For a directory, `override` describes structural
presence; corresponding directories still merge. When `sweep` says
`create stratum is empty`, the local stratum has no entries to reconcile. The
command never deletes anything—remove a reviewed entry through the merged view
or at its real create-stratum path, according to the result you intend.

To inspect the content of an override:

```sh
stratafs diff /bin/sh
```

`diff` compares the create-stratum object with the first lower default. It
supports regular files and symbolic links, reports type changes, refuses other
object types, and bounds each regular-file read to 16 MiB. Binary files are
reported only as different.

## Structured output and status

`list`, `resolve`, and `sweep` accept `--json`. JSON is the stable scripting
interface; it includes the same paths, flags, states, object types, and routing
actions. A non-UTF-8 path is represented losslessly in human output but causes
JSON mode to fail rather than substitute a lossy name.

Exit status has probe-friendly meaning:

| Status | Meaning |
|---|---|
| `0` | Success; for `sweep`, no entries; for `diff`, no difference. |
| `1` | `sweep` found entries or `diff` found a difference. |
| `2` | Usage, visibility, malformed-state, or operational error. |

## Where to go next

For the generic command that creates this and other mounts, read
[`mount`](~peios/mount-policies/mount). For how access to every real object is
decided, start with [File access](~peios/file-access/overview).
