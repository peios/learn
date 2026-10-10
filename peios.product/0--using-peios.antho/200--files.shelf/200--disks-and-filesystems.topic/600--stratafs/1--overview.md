---
title: StrataFS
type: how-to
description: Inspect a StrataFS stack, trace a merged path, compare local overrides and check write-routing and security limits.
related:
  - peios/disks-and-filesystems/overview
  - peios/mount-policies/mount
  - peios/file-access/overview
  - peios/developing-for-peios/writing-boot-hooks/writing-a-boot-hook
---

Use `stratafs` to find which real file supplies a merged path, where a write
would go, and whether local changes hide a packaged default. Start with the
read-only inspector before removing an override or changing a stack.

StrataFS presents ordinary directories as one view while leaving their real
paths independently manageable. Highest precedence wins for each name.
Directories merge; a non-directory provider masks lower objects of that name,
including a lower directory's subtree.

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


## Check permissions and unexpected results

- If an inspection fails, check access to every participating real directory.
  The inspector runs with your rights and fails rather than presenting an
  incomplete protected view. It does not elevate your token.
- If deleting a local entry exposes a packaged file, that is the documented
  no-whiteout behaviour. Use `resolve` and `diff` before removing the override.
- A routing answer is not permission to mutate. `write: copy_up` still needs
  the actual KACS checks and a usable create stratum.
- If a direct stratum path works but its merged path is denied, check stored
  SDs. StrataFS's [fixed deny-missing
  contract](~peios/advanced-peios/peios-kernel/stratafs/security/mount-policy)
  does not use a lower mount's synthesis policy to repair a missing descriptor.
  This conflicts with the general stacking description in [SD storage by
  filesystem](~peios/mount-policies/sd-storage-by-filesystem#stacked-filesystems-overlayfs-and-stratafs).
- For a copied-up file, check preservation rather than assuming ordinary
  creation inheritance. The [StrataFS copy-up
  contract](~peios/advanced-peios/peios-kernel/stratafs/security/copy-up-descriptors)
  preserves the source's full descriptor; ordinary new creations inherit.
  A descriptor-preservation failure fails the copy-up.

For kernel errors and recovery conditions, use [StrataFS failure
modes](~peios/advanced-peios/peios-kernel/stratafs/failure-modes). For example,
a copy-up made stale by a changed provider requires reopening; an open that
succeeds does not guarantee the first write will succeed.

## A `/bin` example

Suppose `/usr/bin` contains packaged programs and `/lcl/bin` is for local
changes. The command below mounts a new stack at `/bin`; it is a configuration
example, not an inspection command. Check the current stack first and do not
replace a running system view merely to try it out:


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

The `dev.peios.fsbase-stratafs-mount-hooks` package installs the `mount-rootfs-stratafs-base.sh` [boot hook](~peios/developing-for-peios/writing-boot-hooks/writing-a-boot-hook)
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

## Where to go next

For the generic command that creates this and other mounts, read
[`mount`](~peios/mount-policies/mount). For how access to every real object is
decided, start with [File access](~peios/file-access/overview).
