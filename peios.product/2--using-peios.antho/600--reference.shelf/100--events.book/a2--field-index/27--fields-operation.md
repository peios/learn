---
title: "operation.*"
description: "Every field the evman catalogue defines under operation: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `operation`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="operation.adopted"></a>`operation.adopted`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether an operation took over an object that already existed in the
target stratum instead of creating a new one. An adopted object keeps
whatever it already had, so an adoption where a creation was expected is
worth reading closely.

**Carried by:**

No event carries this field yet.

## <a id="operation.anonymous"></a>`operation.anonymous`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether an object was created through the anonymous path, an unnamed
temporary file (`O_TMPFILE`) that has no name in any stratum until it is
linked in.

**Carried by:**

No event carries this field yet.

## <a id="operation.arguments"></a>`operation.arguments`

- **Type:** `uint[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The numeric arguments of the command in `operation.code`, in order, such as
the `prctl` arguments after the option.

**Carried by:**

No event carries this field yet.

## <a id="operation.attempts"></a>`operation.attempts`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many attempts the operation made before it gave up.

**Carried by:**

No event carries this field yet.

## <a id="operation.attributes-copied"></a>`operation.attributes-copied`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The metadata attributes a copy-up carried across from the original object
to the copy. Copy-up carries the modification time, the mode (except on a
symbolic link, whose mode the VFS fixes), the owning UID and GID, and the
extended attributes other than StrataFS's own. The bit assignments are not
yet defined, so this field declares no values until they are.

**Carried by:**

No event carries this field yet.

## <a id="operation.available"></a>`operation.available`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many items existed for the operation to return. Read with
`operation.returned`.

**Carried by:**

No event carries this field yet.

## <a id="operation.bytes"></a>`operation.bytes`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many bytes the operation moved before it stopped. On a Unix stream
socket, a read is cut short where the sender's conveyed identity changes,
and this is the only explanation the reader has for a short read.

**Carried by:**

No event carries this field yet.

## <a id="operation.clone-flags"></a>`operation.clone-flags`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux `CLONE_*` flags a new task was created with. `CLONE_THREAD`
decides whether the new task shares its creator's security state, which
`object.process.shares-security` records.

**Carried by:**

No event carries this field yet.

## <a id="operation.code"></a>`operation.code`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The command or opcode within the operation, such as an `ioctl` command or a
`prctl` option. Its vocabulary depends on `operation.name`, so the two are
read together.

**Carried by:**

No event carries this field yet.

## <a id="operation.compat"></a>`operation.compat`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the call came in through the 32-bit compatibility entry point.

**Carried by:**

No event carries this field yet.

## <a id="operation.contents-copied"></a>`operation.contents-copied`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a copy-up copied an object's contents or only created the node.
Always false for a directory, whose entries are not copied. Read with the
object's type before assuming a copy-up moved any data.

**Carried by:**

No event carries this field yet.

## <a id="operation.copy-up-generation"></a>`operation.copy-up-generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The generation of the current copy-up phase. Incremented each time a phase
is armed, so a handle carrying an older generation is stale. Unrelated to
`object.mount.policy-generation`.

**Carried by:**

No event carries this field yet.

## <a id="operation.copy-up-phase"></a>`operation.copy-up-phase`

- **Type:** `str.enum`
- **Values:** `none` · `source-read` · `create` · `populate` · `publish-link` · `publish-rename` · `cleanup` · `orphan-marker`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The phase of an in-flight StrataFS copy-up. KACS admits the copy-up's own
operations without a caller check only while they match the armed phase,
so a refusal here is a copy-up that tried something its phase does not
allow.

**Carried by:**

No event carries this field yet.

## <a id="operation.create-disposition"></a>`operation.create-disposition`

- **Type:** `str.enum`
- **Values:** `supersede` · `open` · `create` · `open-if` · `overwrite` · `overwrite-if`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What a native open was told to do about an existing or missing file, from
the `KACS_DISPOSITION_*` values. `supersede` and `overwrite` destroy an
existing file's content; `open` fails if the file is missing and `create`
fails if it exists.

**Carried by:**

No event carries this field yet.

## <a id="operation.create-options"></a>`operation.create-options`

- **Type:** `uint.flags`
- **Values:** `0x1 DIRECTORY` · `0x2 DELETE_ON_CLOSE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The create options of a native open, from the `KACS_CREATE_OPT_*` bits.
`DELETE_ON_CLOSE` schedules the file's removal when the last handle that
requested it is closed.

**Carried by:**

No event carries this field yet.

## <a id="operation.decision"></a>`operation.decision`

- **Type:** `str.enum`
- **Values:** `primary` · `parent-fallback` · `source` · `dest` · `delete-existing`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which sub-decision of a namespace operation the record concerns, from the
`KACS_NS_*` codes. A single-decision operation reports `primary`; a delete
refused on the object can still be allowed by `DELETE_CHILD` on the
parent, `parent-fallback`; a rename produces up to three records, for the
source, the destination parent, and an existing destination it replaces.

**Carried by:**

No event carries this field yet.

## <a id="operation.duration"></a>`operation.duration`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How long the operation took.

**Carried by:**

No event carries this field yet.

## <a id="operation.entry-point"></a>`operation.entry-point`

- **Type:** `str.enum`
- **Values:** `mount` · `directory-open` · `rmdir` · `staging-lookup` · `copy-up`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The operation that set off recovery of orphaned staging entries, the
partial copies an interrupted copy-up leaves in the create stratum.
`mount` sweeps the create stratum's root when the mount is made;
`directory-open` and `rmdir` sweep the directory concerned; `copy-up`
sweeps the destination's parent first; `staging-lookup` fires when a path
lookup names an entry that looks like a staging name.

`staging-lookup` is the one an unprivileged process can trigger at will,
by looking up such a name.

**Carried by:**

No event carries this field yet.

## <a id="operation.exec-unsafe"></a>`operation.exec-unsafe`

- **Type:** `uint.flags`
- **Values:** `0x1 LSM_UNSAFE_SHARE` · `0x2 LSM_UNSAFE_PTRACE` · `0x4 LSM_UNSAFE_NO_NEW_PRIVS`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The kernel's unsafe-exec flags (`bprm->unsafe`) at an exec. Under
`PTRACE` or `NO_NEW_PRIVS`, an exec may not raise the process's trust, and
a signature-derived label is capped instead.

**Carried by:**

No event carries this field yet.

## <a id="operation.failed-count"></a>`operation.failed-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many items in a batch operation failed. With
`operation.succeeded-count`, the whole batch; a non-zero count here on a
record whose `outcome.success` is true is a partial success.

**Carried by:**

No event carries this field yet.

## <a id="operation.fd"></a>`operation.fd`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The file descriptor a bulk operation transferred through — the sink a
backup was written to, or the source a restore was read from. Direction is
given by the event, not by this field.

**Carried by:**

- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started)
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started)

## <a id="operation.gid"></a>`operation.gid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The GID a `setgid`-family call asked for.

**Carried by:**

No event carries this field yet.

## <a id="operation.linux-projection"></a>`operation.linux-projection`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the Linux identity projection — UID, GID and supplementary groups —
was recomputed as part of a token install. False means the process's Linux
credentials still reflect the previous token.

**Carried by:**

No event carries this field yet.

## <a id="operation.lsm-flags"></a>`operation.lsm-flags`

- **Type:** `uint.flags`
- **Values:** `0x1 LSM_SETID_ID` · `0x2 LSM_SETID_RE` · `0x4 LSM_SETID_RES` · `0x8 LSM_SETID_FS`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which variant of a legacy set-identity call was made, as the kernel's
`LSM_SETID_*` flags: `setuid`, `setreuid`, `setresuid` or `setfsuid`, and
the `gid` equivalents. 0 for `setgroups`.

**Carried by:**

No event carries this field yet.

## <a id="operation.name"></a>`operation.name`

- **Type:** `str.enum`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which operation was attempted. Each event declares the names its
enforcement point uses, and the sets are disjoint where two points could
be confused: FACS names operations on an already-open handle with a
`file.` prefix, and StrataFS names its own without one.

**Carried by:**

- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="operation.name-truncated"></a>`operation.name-truncated`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a name in the record could not be carried in full and was cut
short. When true, do not search for the name exactly: the full name is
longer than what the record holds.

**Carried by:**

No event carries this field yet.

## <a id="operation.non-blocking"></a>`operation.non-blocking`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a path walk was in RCU mode, the kernel's non-blocking lookup.
StrataFS refuses every RCU-mode step, so the kernel retries the walk in
blocking mode; a record with this set is the refusal, not a failure the
caller sees.

**Carried by:**

No event carries this field yet.

## <a id="operation.open-flags"></a>`operation.open-flags`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The `open` flags the caller asked for, as the Linux `O_*` bits of the
`flags` argument. The rights these imply are what KACS checks;
`access.requested-minimum` records the least of them.

**Carried by:**

No event carries this field yet.

## <a id="operation.open-flags-effective"></a>`operation.open-flags-effective`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The open flags StrataFS used against the stratum below, after rewriting
the flags the caller asked for, which `operation.open-flags` holds and
whose `O_*` values decode this one too. Where the object is not written in
place, a write open of a regular file is reopened read-only without
`O_APPEND`, and `O_TRUNC` is dropped, until a write copies the object up.

The difference between the two fields is the finding: a caller that asked
to truncate a file may hold a descriptor on which nothing has been
truncated yet.

**Carried by:**

No event carries this field yet.

## <a id="operation.profiling-scope"></a>`operation.profiling-scope`

- **Type:** `str.enum`
- **Values:** `single-process` · `system-wide`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The scope of a profiling authorisation. `system-wide` samples every
process, PIP-protected ones included, and needs `SeSystemProfilePrivilege`;
`single-process` profiles one other process and needs
`SeProfileSingleProcessPrivilege`.

**Carried by:**

No event carries this field yet.

## <a id="operation.ptrace-initiator"></a>`operation.ptrace-initiator`

- **Type:** `str.enum`
- **Values:** `tracer` · `tracee`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which side began a ptrace relationship. `tracer` is a debugger attaching
to another process; `tracee` is a process inviting its parent to control
it, with `PTRACE_TRACEME`.

**Carried by:**

No event carries this field yet.

## <a id="operation.reentry-depth"></a>`operation.reentry-depth`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The nesting depth of the kernel's own re-entry into descriptor storage: a
read or write of a descriptor attribute that passes back through the
security hooks, as happens through a stacking filesystem. Not the depth of
a directory walk, which is `object.sd.synthesis-depth`.

**Carried by:**

No event carries this field yet.

## <a id="operation.rename-flags"></a>`operation.rename-flags`

- **Type:** `uint.flags`
- **Values:** `0x1 RENAME_NOREPLACE` · `0x2 RENAME_EXCHANGE` · `0x4 RENAME_WHITEOUT`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The flags a caller passed to `renameat2`. StrataFS always refuses
`RENAME_WHITEOUT` with `EINVAL`, so a record carrying that bit is a
refusal however the rest of the rename looked.

**Carried by:**

No event carries this field yet.

## <a id="operation.replaced"></a>`operation.replaced`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the operation silently replaced something that was already there,
such as a link between tokens that displaced an existing pair.

**Carried by:**

No event carries this field yet.

## <a id="operation.returned"></a>`operation.returned`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many items the operation returned. Fewer than `operation.available`
means the result was truncated.

**Carried by:**

No event carries this field yet.

## <a id="operation.route"></a>`operation.route`

- **Type:** `str.enum`
- **Values:** `in-place` · `copy-up` · `read-only`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How StrataFS routed a mutation of an existing object. `in-place` wrote the
object in the stratum that provides it. `copy-up` first copied it into the
create stratum and wrote the copy. `read-only` refused it with `EROFS`,
because the object's stratum does not accept writes and no copy-up was
possible.

`read-only` has several causes, among them a read-only mount, no create
stratum, and an object that cannot be copied, and this field does not say
which.

**Carried by:**

No event carries this field yet.

## <a id="operation.setattr-mask"></a>`operation.setattr-mask`

- **Type:** `uint.flags`
- **Values:** `0x1 ATTR_MODE` · `0x2 ATTR_UID` · `0x4 ATTR_GID` · `0x8 ATTR_SIZE` · `0x10 ATTR_ATIME` · `0x20 ATTR_MTIME` · `0x40 ATTR_CTIME` · `0x80 ATTR_ATIME_SET` · `0x100 ATTR_MTIME_SET` · `0x200 ATTR_FORCE` · `0x400 ATTR_CTIME_SET` · `0x800 ATTR_KILL_SUID` · `0x1000 ATTR_KILL_SGID` · `0x2000 ATTR_FILE` · `0x4000 ATTR_KILL_PRIV` · `0x8000 ATTR_OPEN` · `0x10000 ATTR_TIMES_SET` · `0x20000 ATTR_TOUCH` · `0x40000 ATTR_DELEG`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which attributes a setattr asked to change, as the kernel's `ATTR_*` bits.
These bits are internal to the Linux kernel rather than part of its ABI,
so they are decoded against the kernel version that wrote the record.
`ATTR_SIZE` with `ATTR_OPEN` is a truncate from `open` with `O_TRUNC`, not
an explicit `truncate` call.

**Carried by:**

No event carries this field yet.

## <a id="operation.settled-view"></a>`operation.settled-view`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a record concerns a directory view settled when its descriptor was
opened, rather than a live resolution of the merged path. A settled view
keeps the listing and strata it was opened with, and goes on answering
from them after a rename and when the descriptor is passed to another
process, so it can disagree with what the path resolves to now.

**Carried by:**

No event carries this field yet.

## <a id="operation.signal"></a>`operation.signal`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The signal number of a signal delivery decision. The signal decides which
process right is required, so a refusal is read with it.

**Carried by:**

No event carries this field yet.

## <a id="operation.site"></a>`operation.site`

- **Type:** `str.enum`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which system call or kernel gate the record came from. Peios adds about
thirty access checks to Linux call sites — many of them re-checks on an
already-open file descriptor, added because an open descriptor used to be a
way round the check — and a refusal is only useful if it says which one
fired. Each event declares the sites it can come from.

**Carried by:**

No event carries this field yet.

## <a id="operation.stacked-create"></a>`operation.stacked-create`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the object's real inode was created by a stacking filesystem
below StrataFS rather than directly by the stratum's own filesystem. When
true, a different filesystem's hooks ran on the creation, which changes
which hook stamped the object's security descriptor.

**Carried by:**

No event carries this field yet.

## <a id="operation.stage"></a>`operation.stage`

- **Type:** `str.enum`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which internal stage of a multi-step operation the record concerns.
Several unrelated operations have stages, with nothing in common between
their vocabularies, so each event declares its own.

**Carried by:**

No event carries this field yet.

## <a id="operation.stage-requested"></a>`operation.stage-requested`

- **Type:** `str.enum`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The stage that was asked for while another, `operation.stage`, was still
active. Drawn from the same vocabulary as `operation.stage` on the same
event, which declares it.

**Carried by:**

No event carries this field yet.

## <a id="operation.strata"></a>`operation.strata`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The set of strata taking part in a merged operation, as flags with one bit
per stratum:
bit 0 is the stratum at index 0, the highest-precedence one. A merged
directory's listing, for example, draws on every stratum whose bit is set.

**Carried by:**

No event carries this field yet.

## <a id="operation.succeeded-count"></a>`operation.succeeded-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many items in a batch operation succeeded.

**Carried by:**

No event carries this field yet.

## <a id="operation.timeout"></a>`operation.timeout`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The timeout that applied to the operation. On an operation that timed
out, `operation.duration` will have reached it.

**Carried by:**

No event carries this field yet.

## <a id="operation.uid"></a>`operation.uid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The UID a `setuid`-family call asked for. Peios does not let such a call
change identity; the record shows what was attempted.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
