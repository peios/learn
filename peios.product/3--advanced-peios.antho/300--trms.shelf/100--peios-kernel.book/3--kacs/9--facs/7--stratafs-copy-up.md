---
title: The StrataFS Copy-Up Context
description: Copy-up is the internal realisation of an already-authorized operation — its admission and lifetime, object and phase binding, and exempt operations.
---

StrataFS copy-up is the internal realisation of an operation already
authorized against a StrataFS handle — not a second caller-requested
operation. KACS therefore provides a kernel-internal context so that
the mechanics of copy-up introduce no new rights checks against the
task that happens to execute them.

The context exempts **KACS caller authorization only**. It does not
replace credentials, borrow an identity, grant a privilege, bypass
another LSM, neutralise an underlying filesystem check, make a
read-only mount writable, or suppress immutable, append-only, quota,
space, I/O or format errors. Every exemption is a return before the
authorize call, and every mutation still goes through the ordinary
`vfs_*` path under `mnt_want_write()`.

## Admission and lifetime

Only the in-kernel StrataFS implementation can create or enter a
context. There is no userspace surface of any kind — no ABI, file
descriptor, token, ioctl, syscall or securityfs control — and the
copy-up API is declared in a kernel-private header with no exported
symbols.

A context is created only after the StrataFS operation requiring
copy-up has passed its complete outer authorization. KACS does not
verify that: the context creation call performs no check, and the
ordering is satisfied by StrataFS calling in the right order. The
context is not itself an alternative authorization path.

The exemption covers namespace creation the outer handle authorises
without an add-entry right on the create stratum, so the context is
reachable only from a create-enabled mount established by a caller
holding `CAP_SYS_ADMIN` in the **initial** user namespace. That
closure rests on an explicit test of the mounter's user namespace at
stack establishment — the capability half contributes nothing to it,
because the KACS switchboard discards the target namespace and answers
from `SeTcbPrivilege` alone (§3.10.2). The check is made when the
immutable stack is established rather than when a copy-up runs, so
descriptor delegation cannot reintroduce acting-task authorization.
Reconfiguration cannot re-supply the strata list.

A context attaches to at most one task, and a task carries at most
one. It is not inherited by `fork()`, `clone()` or `execve()` — exec
explicitly clears it. A refcounted context can be transferred to a
kernel worker, but the originating task leaves it first. Leaving,
task exit, every error path, and completion all remove the attachment
and clear any armed phase.

The interface fails closed on nesting, concurrent attachment, a stale
phase, or an object mismatch. A mismatched operation is evaluated
normally and neither consumes nor broadens the armed exemption.

## Object and phase binding

Creation pins the exact provider path, its current inode, a complete
validated copy of its effective descriptor, and the provider-visible
`security.capability` value or its absence. Every later positive path
is paired with a pinned inode as well — retaining a dentry alone is
insufficient, because an unlink followed by recreation can
reinstantiate it over a different inode.

One phase is armed at a time:

| Phase | Objects admitted |
|---|---|
| Source read | The pinned provider only. |
| Create | One pinned provider, one destination parent, and either one named negative dentry or one anonymous creation in that parent. Used for both parent materialisation and the staged object. |
| Populate | The pinned provider and the one staged object bound to the context. |
| Publish by link | The bound staged object, one destination parent, one absent destination dentry. |
| Publish by rename | The bound staged object and its parent, one destination parent, one absent destination dentry. |
| Cleanup | One bound staging or materialisation dentry and its exact parent. |
| Orphan cleanup | One positive provider dentry carrying an authenticated stale staging marker, and its exact parent. |
| Orphan-marker cleanup | The exact positive provider dentry whose authenticated stale marker is being removed after publication. |

Path, dentry, inode, parent, object type and operation kind are all
compared wherever the hook supplies them — and path comparison
includes the mount, so the same dentry reached through a different
mount of the same superblock does not match. An inode-only hook can
match the pinned inode, but that does not authorize a pathname
operation on another dentry, and a phase never acts as a wildcard for
other objects of the same filesystem or directory.

The staged binding stays valid only while its dentry names the pinned
inode under the pinned staging parent, and that parent still names its
own pinned inode. A rename or parent substitution invalidates the
populate, protected-metadata and publish exemptions even when the
staged dentry and inode are themselves unchanged.

Named creation is bound to the exact final component. Anonymous
creation is bound to its parent, expected object type, the attached
task, and the single armed create phase — and once created, the
anonymous object has to be bound as the staged object before populate,
publish or cleanup can use it.

Where the destination is a stacking filesystem creating a real inode
below the armed destination dentry, the transition is authenticated at
the exact outer dentry, and only the one subsequent real-inode
security initialisation of the expected type receives the pinned
provider descriptor. The real inode is not the staged binding: the
outer inode is separately anchored, through the matching post-create
event for an anonymous object or an explicit confirmation of the exact
positive outer dentry for a named one. A missing, repeated, mismatched
or out-of-order transition fails closed, and an inner post-create
event from the real filesystem is rejected as the outer anchor by
superblock comparison.

KACS retains the exact path, inode, parent path and parent inode of
every named object whose creation it admits. Cleanup can be armed only
for one of those or for the exact bound staging object; an unrelated
positive dentry fails with `ESTALE`. The cleanup setup call is not
itself authority to choose a deletion victim.

After an atomic rename or link publishes the staged inode, the staging
identity can be rebound to the published path, but only while mount,
inode, parent dentry and pinned parent inode all still match. The
rebind API exists and is **not called** by StrataFS: the link case is
rebound internally by the publish path, and the rename case relies on
publish preserving the dentry. That holds because publication always
renames within a single parent. A cross-directory publish rename would
silently invalidate the staging binding, since the rename-publish
entry point does not require the destination parent to equal the
staging parent — currently unreachable, but the guard is the caller's
discipline rather than the interface's.

Named staging entries carry `security.peios.stratafs_staging`.
Caller-originated writes and removals of it are denied. A write or
removal is admitted only on the exact bound staging inode during
populate, or on the exact orphan-marker object during authenticated
recovery — where the predicate admits a *write* as well as a removal,
being shared between the setxattr and removexattr hooks. Probing the
marker for recovery is a kernel-only raw read conveying no caller
authority, and orphan deletion is bound to the exact dentry, inode,
parent dentry and parent inode supplied when the phase was armed, so
an arbitrary name sharing the staging prefix never matches. Recovery
processes at most 128 entries per batch.

## Exempt operations

For a matching object in a matching phase, the ordinary AccessCheck,
cached-grant check, privilege check and caller-access audit decision
are omitted at these points:

| Copy-up action | Enforcement points |
|---|---|
| Open and read provider data or a symlink target | `security_inode_permission`, `security_file_open`, `security_file_permission`, `security_inode_readlink` |
| Read provider attributes and extended attributes | the inode and file getattr, setattr-preflight, getxattr and listxattr paths as applicable |
| Create a staged file, directory or symlink, and materialise parents | `security_inode_permission`, `security_inode_create`, `security_inode_mkdir`, `security_inode_symlink`, `security_inode_init_security`; for a stacking destination also `security_dentry_create_files_as` and, for an anonymous object, `security_inode_post_create_tmpfile` |
| Populate staged data, attributes and eligible non-descriptor xattrs | `security_inode_permission`, `security_file_open`, `security_file_permission`, the inode and file setattr paths, setxattr and removexattr. `security.capability` uses only the dedicated clone call below. |
| Publish | `security_inode_permission` on the exact staged object or destination parent, then `security_inode_link` or `security_inode_rename` |
| Remove staging or roll back materialised entries | `security_inode_permission` on the exact parent, then `security_inode_unlink` or `security_inode_rmdir` |

A `security_inode_permission` or `security_file_permission` match also
matches the requested mask. Provider access is
read-only — write, append and non-directory execute requests never
match it. Staging access is limited to the read, write and append
masks population needs, plus execute and chdir for directories, and
namespace parents to the write and traverse masks the one armed action
needs, plus open and chdir. Unknown mask bits fail closed.

The list is exhaustive. The context does not exempt execution, memory
mapping, ioctl, locking, arbitrary `fcntl`, device access, process
access, socket access, mount operations, or operations on a descriptor
installed into a userspace file table — each verified by the absence
of any copy-up branch on those paths. Internal copy-up files are
additionally denied `statfs`, `truncate`, `fsync` and `fallocate`.

A file opened internally under the exemption is marked
copy-up-internal in its blob and carries a granted mask of zero. It is
usable without a cached caller grant only while the same context is
attached and its phase admits that exact file. Use after phase
completion, from another task, or after transfer through `SCM_RIGHTS`
fails closed. Each armed phase has a distinct monotonically increasing
generation — overflowing it fails closed — and an internal file is
sealed to the generation it was opened in, so a later phase of the
same kind after a worker transfer cannot reactivate an older file.
Final release drops the context reference.

The one exception is the read-only provider-directory cursor used by
bounded staging recovery. StrataFS may retain that file while it
leaves the context to clean one captured batch, then resume it after
re-entering the same context and arming a new source-read phase. Only
a directory file already marked internal for that exact context, still
naming the pinned provider path and inode, opened for read without
write, execute or path-only mode, and inside that attached
source-read phase, resumes; it is then resealed to the new generation.
Between phases it is unusable and conveys no deletion authority.

## Backing-file adoption

Once a regular-file copy is published, one exact copy-up-internal
backing file can become the backing file for the outer StrataFS open
description. The staging binding is verified, and the backing file's
recorded user path is confirmed to be that same outer description;
the outer description's immutable granted and continuous-audit
snapshot is then copied across and the internal marker removed. This
is a transfer of authority already attached to the descriptor, not a
new AccessCheck against the task that caused the copy-up, which is
what preserves descriptor delegation when that task is not the opener.
It is one-shot, and requires the backing file mode.

The ordering is worth noting: StrataFS performs the adoption **before**
publishing the anonymous staged object rather than after, so what is
verified is the still-bound staging binding rather than a published
one.

## Deferred deletion

Delete-on-close is authorized when armed and recorded on the open file
description (§3.9.2). At final close there is no re-authorization
against the closing task. Instead a synchronous, non-nesting internal
deletion scope is armed for that exact outer file, and StrataFS binds
it once to the exact provider parent, dentry and inode selected from
the descriptor's settled provider. Only the corresponding outer and
lower unlink calls match, and the scope is cleared on every return.

The mechanism never turns an ordinary close into deletion authority,
never admits a different provider entry, and never permits unlinking
an entry that no longer names the descriptor's inode. If the original
entry has disappeared or changed identity, the deletion is already
complete and no exemption is used.

## Exact protected-metadata cloning

KACS owns descriptor cloning rather than StrataFS raw-xattr code.
Before a create phase is armed, the provider's complete effective
descriptor is resolved and pinned using the ordinary mount-policy and
corrupt-descriptor rules (§3.9.5). A missing, corrupt, unresolvable,
oversized or unsupported descriptor fails the phase before the
destination is created.

For a matching inode security initialisation, an exact byte-for-byte
copy of the pinned descriptor is installed instead of inheritance
running. The canonical xattr is installed as part of inode creation
and the inode's validated parsed cache is seeded from identical bytes
before the inode becomes usable. Failure to allocate, validate or
install either representation fails creation — there is no window in
which a named staging inode carries an inherited or otherwise weaker
descriptor.

On a stacking destination the same applies to the real inode created
below the outer dentry, with the authenticated outer transition as the
only authority to redirect installation there. The pinned bytes are
installed and cached during the real inode's creation, before the
outer object is confirmed or bound; inheriting the parent's descriptor
and repairing it afterwards would not be conforming.

The canonical descriptor is not copied by ordinary xattr enumeration —
it is reported as cancelled so a stacking filesystem discards it — and
raw canonical getxattr and setxattr stay denied even inside the
context, with the hook-side denial evaluated before any phase match.
The context does not override the unconditional denial of POSIX ACL
mutation either.

Raw setxattr, including through an internal copy-up file, remains
unable to install `security.capability`. Where the provider has one,
StrataFS calls the dedicated clone entry point during populate, after
any operation that might clear file capabilities. That call accepts
only a kernel buffer exactly matching the pinned value, under the same
user namespace it was pinned in, for the still-bound staged inode. It
re-reads the provider immediately before installing and fails with
`ESTALE` if the value or its presence changed.

The call copies the caller's buffer before comparing, and installs
with `XATTR_CREATE` through the ordinary VFS path, so mount-idmap
conversion, xattr validation, filesystem permission and format checks
and other LSM checks all still apply. The otherwise-dead
`CAP_SETFCAP` gate is satisfied only synchronously inside that
validated call, and the corresponding setxattr re-entry is admitted
only after the first hook matches the exact staged inode. The
capability answer targets only the pinned caller namespace or the
staged inode's filesystem namespace, and the condition is cleared on
every return. Nothing is installed when the provider had no attribute,
a different one, or an unreadable or invalid one. The exception does
not revive exec-time file-capability grants.

There is one asymmetry here: the removal path does not reject
`security.capability` the way the set path does, so an internal
copy-up descriptor can remove it from the staged object during
populate.

Other eligible provider xattrs follow StrataFS's replication rules
while KACS's caller checks on their source and staging objects are
exempted as above. An ineligible xattr that cannot be replicated
triggers StrataFS's ordinary copy-up failure rule rather than being
silently omitted.

## Auditing

The outer authorized handle operation remains subject to ordinary
audit. No second caller AccessCheck or privilege-use audit is emitted
for an exempt internal sub-operation, since that would attribute
StrataFS mechanics to a caller decision that never happened — and
internal files carry a continuous-audit mask of zero, so they generate
no per-operation events either. The `CAP_SETFCAP` satisfaction path
returns before the capability check that would record privilege use.

StrataFS decides when its own copy-up lifecycle and failure events
occur; KACS supplies the kernel-only emitter, so KMES stamps each
event with the effective token of the task whose operation caused it
(§2.2). Two of those emissions are best-effort: an allocation failure,
or an operation string that is empty or over 64 bytes, drops the event
silently.

Denied mismatches, and operations performed with no active matching
context, follow the ordinary authorization and audit paths.
