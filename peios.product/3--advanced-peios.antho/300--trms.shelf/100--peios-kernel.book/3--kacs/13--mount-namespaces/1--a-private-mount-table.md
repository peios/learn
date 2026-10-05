---
title: A Private Mount Table
description: A mount namespace is a KACS object — any process may create one without privilege, and what it may then do to its own mount table is decided by the namespace's security descriptor, not by a capability manufactured in a user namespace.
---

A mount namespace is a private copy of the kernel's mount table: the
map from directory paths to the filesystems mounted there. Linux
answers "who may change this table" with `CAP_SYS_ADMIN` in the user
namespace that owns it, and lets an unprivileged process manufacture
that capability by creating a user namespace first — which is how
bubblewrap, and every unprivileged container tool built the same way,
gets a private root.

On Peios that route leads nowhere. The capability switchboard discards
the target user namespace and answers from the token's privileges
alone (§3.10.2), so being root in a user namespace confers nothing, and
`CAP_SYS_ADMIN` maps to `SeTcbPrivilege`. KACS answers the question the
way it answers every other: the mount namespace is an object with a
security descriptor, and changing it is an access check. [*mntns.object-model]

## The object

Every mount namespace other than the initial one carries a security
descriptor, minted in `copy_mnt_ns()` from the creating task's effective
token and released when the namespace is. [*mntns.descriptor-lifetime] The initial namespace, and the
anonymous namespaces `open_tree(OPEN_TREE_CLONE)` and `fsmount` create
for detached trees, carry none. [*mntns.initial-has-no-descriptor]

The minted descriptor names its creator and nobody else: owner and
group come from the token, and the DACL is a single allow ACE granting
the creator's user SID `GENERIC_ALL`. [*mntns.default-descriptor] `SYSTEM` and
`BUILTIN\Administrators`, which the SysV IPC and socket defaults name,
are absent on purpose — the privilege rung of the mount gate admits them
before the descriptor is read, so an ACE would only pretend the
descriptor was what let them in.

The rights are those of `<pkm/mntns.h>`:

| Right | Grants |
|---|---|
| `KACS_MNTNS_MOUNT` | changing the table: a bind mount, an unmount, `pivot_root` |
| `KACS_MNTNS_ENTER` | joining the namespace with `setns` — defined so the descriptor's meaning is fixed; no code consults it yet, and `setns` into a mount namespace still needs `SeTcbPrivilege` |
| `READ_CONTROL`, `WRITE_DAC`, `WRITE_OWNER` | the standard rights, which `KACS_MNTNS_ALL_ACCESS` includes; nothing exposes a namespace's descriptor to `kacs_get_sd` or `kacs_set_sd` yet |

The generic mapping: `GENERIC_WRITE` is `KACS_MNTNS_MOUNT` and
`WRITE_DAC`; `GENERIC_EXECUTE` is `KACS_MNTNS_ENTER` and `READ_CONTROL`;
`GENERIC_READ` is `READ_CONTROL` alone, there being nothing to read from
a namespace beyond its descriptor; `GENERIC_ALL` is
`KACS_MNTNS_ALL_ACCESS`. [*mntns.generic-mapping]

## Creating one

`unshare(CLONE_NEWNS)`, and `clone` with `CLONE_NEWNS`, need no
privilege when the mount namespace is the only namespace requested. [*mntns.create-unprivileged]
Every other namespace type — and any combination that includes one —
keeps the `CAP_SYS_ADMIN` gate in `kernel/nsproxy.c`, which the
switchboard answers with `SeTcbPrivilege`. [*mntns.other-types-stay-gated] A user namespace may still be
created alongside, as upstream allows; it changes nothing about what
follows.

A table created by a task that does not hold the mount privilege
receives its mounts as *slaves* of the parent table's, exactly as
upstream does for a copy owned by a different user namespace:
propagation runs parent to child only, so whatever the creator mounts
in its own table never appears in the one it copied. [*mntns.unprivileged-copy-is-slave] A table created
with the privilege is copied as upstream copies it, peers and all.

## The mount gate

`may_mount()` in `fs/namespace.c` is the gate for `mount`, `umount2`,
`pivot_root`, `open_tree(OPEN_TREE_CLONE)`, `fsmount`, `move_mount` and
`mount_setattr`, and for `fsopen` and `fspick` in `fs/fsopen.c`.
`mount_capable()` in `fs/super.c` is the second
gate a new filesystem passes, when its superblock is brought into being.
Under KACS both take the operation as an argument, with the filesystem
type where one is being created, and ask `pkm_kacs_may_mount_op()` in
three rungs, against the caller's effective token and the descriptor of
the caller's current namespace: [*mntns.gate-rungs]

1. **Privilege.** A token holding `SeManageVolumePrivilege` or
   `SeTcbPrivilege`, enabled, is admitted to every operation in every
   namespace, and the privilege is marked used. This rung is decided
   first and alone: a token that holds the privilege never reaches the
   descriptor, and a token that does not is never asked the privilege
   question, so an unprivileged caller's routine bind mount records no
   privilege refusal. [*mntns.gate-privilege-first]
2. **No descriptor.** In a namespace with no descriptor — the initial
   one — nothing else admits anything. This is the whole of the rule that
   the root table keeps: without the privilege, no process changes it. [*mntns.root-table-privilege-only]
3. **Descriptor.** Otherwise, and only for an operation the descriptor
   can admit, AccessCheck for `KACS_MNTNS_MOUNT` runs against the
   namespace's descriptor under the caller's PIP context, exactly as it
   does for a socket or a SysV object. [*mntns.gate-descriptor-check]

The operations the descriptor can admit are the ones that put no
kernel filesystem parser of an untrusted image in reach of the caller: [*mntns.admissible-operations]

| `mount(2)` shape | Gate operation | Admissible by descriptor |
|---|---|---|
| `MS_BIND`, with or without `MS_REC` | bind | yes |
| `umount2` without `MNT_FORCE` | unmount | yes |
| `pivot_root` | pivot_root | yes |
| a new `tmpfs`, `proc` or `stratafs` (`do_new_mount`) | new filesystem | yes |
| any other filesystem type | new filesystem | no |
| `MS_REMOUNT`, including `MS_REMOUNT\|MS_BIND` | other | no |
| `MS_MOVE`; `MS_SHARED`, `MS_PRIVATE`, `MS_SLAVE`, `MS_UNBINDABLE` | other | no |
| `open_tree(OPEN_TREE_CLONE)`, `fsopen`, `fspick`, `fsmount`, `move_mount`, `mount_setattr` | other | no |

The filesystem types a descriptor can admit are an allowlist KACS keeps,
and it holds exactly `tmpfs`, `proc` and `stratafs`: all three read
nothing but the caller's own mount options. tmpfs has no backing image,
proc is a view of the kernel's own state, and stratafs is a view of
directories the caller can already traverse, every access through it
decided on the providing object (§4.6.1). A type that parses an image —
ext4, squashfs, iso9660, ntfs3 — is refused before the type is even
looked up. The list is an attack-surface list and not a policy knob:
who may change a table is decided by the table's descriptor alone, and
the same descriptor that admits tmpfs refuses ext4. [*mntns.fs-type-allowlist]

A stratafs stack admitted this way is read-only or absent-tolerant.
stratafs's own admission (§4.2.3) refuses a `create` stratum to any
caller outside the initial user namespace or without `CAP_SYS_ADMIN`,
which is `SeTcbPrivilege`, and that test runs after the gate, so an
unprivileged caller that asks for one gets `EPERM` from stratafs
whatever its table's descriptor grants. Copy-up carries no add-entry
right of its own, which is why a writable stack is authority in itself
and stays with the TCB; a private table's writable paths are tmpfs, or
bind mounts of directories the caller owns. [*mntns.stratafs-read-only-only] Admitting the type does put
stratafs's option parser and stack validation in reach of unprivileged
input for the first time; both fail closed with `EINVAL` on a relative
stratum, a duplicate, `create` combined with `ro`, an empty stack or
more than sixteen strata, and with `ENOENT` on a missing stratum not
marked `am`.

Everything in the *no* rows needs the privilege whatever the descriptor
grants, and `MNT_FORCE` additionally keeps its own `CAP_SYS_ADMIN` test
on the superblock's user namespace. A mount that the gate admits still
goes through every check upstream applies afterwards: the bind source is
looked up through the caller's own table, an unmount needs a mount
point that belongs to it, and `pivot_root` needs the propagation
conditions it always needed, which the slave copy of an unprivileged
table satisfies.

### An unprivileged tmpfs is stamped for its creator

A fresh tmpfs is deny-missing under FACS (§3.9.5): nothing on it carries
a descriptor, so nothing on it is reachable until someone sets the
superblock's mount policy, which `kacs_set_mount_policy` reserves to the
mount privilege. That is right for the system's own overlays, which are
seeded deliberately, and it would leave a tmpfs admitted by a namespace
descriptor permanently empty. So at `sb_kern_mount`, a tmpfs brought
into being by a token that holds no mount privilege is stamped
synthesize-ephemeral with a template descriptor the kernel mints itself:
owner and group from the mounter's token, one allow ACE granting the
mounter's user SID `GENERIC_ALL` — the same shape as the namespace
descriptor. [*mntns.unprivileged-tmpfs-stamped] The policy generation moves to 1, which retires the
deny-missing default the root inode's creation cached during
`fill_super`. The mounter cannot choose the template, and a superblock
whose policy `kacs_set_mount_policy` has already set is left alone. A
privileged mounter's tmpfs is untouched: it keeps the magic default and
the mounter seeds it, as before. [*mntns.privileged-tmpfs-untouched] proc is unmanaged and needs no
stamp; a second proc mount in the same pid namespace shows the same
processes under the same per-process checks.

So a process whose whole world is a directory of its choosing is:

```
unshare(CLONE_NEWNS);
mount(dir, dir, NULL, MS_BIND, NULL);
chdir(dir);
pivot_root(".", ".");
umount2(".", MNT_DETACH);
chdir("/");
```

with no user namespace and no privilege. [*mntns.private-root-sequence] The bind makes the directory a
mount point, which `pivot_root` requires; pivoting onto the same path
stacks the old root on the new one, and detaching `.` drops it.

## What the object does not change

The token never changes at `exec` (§3.10.3), so a program run inside a
private table has exactly the authority of the process that built it,
and a fake `/etc` fools nobody but its author. Every access to a file
reached through a bind mount is decided on the real object's
descriptor, so a bind mount shows a name and denies at open. The
kernel's own helpers — `modprobe` and its kin — are executed in the
initial namespace and refused unless TCB-signed (§3.7). A signed
binary's PIP tier is derived from the binary and not from the table it
was found in, and library verification, where a process enables it,
compares signatures at `mmap` rather than paths. [*mntns.no-new-authority]

## Tracing

The `kacs:kacs_mntns` event records a descriptor minted at namespace
creation, each rung of the gate, and a tmpfs stamped for its creator,
with the operation code, the right asked of the descriptor where a rung
reached it, a reason from `<pkm/trace.h>` — `sd-alloc`, `sd-alloc-fail`,
`gate-privilege`, `gate-no-sd`, `gate-op-not-admitted`,
`gate-sd-decision`, `gate-pip-context`, `gate-fs-not-admitted`,
`sb-stamp`, `sb-stamp-fail` — and the verdict. [*mntns.trace-event]
