---
title: "object.*"
description: "Every field the evman catalogue defines under object: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `object`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="object.cgroup.generation"></a>`object.cgroup.generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The cgroup generation of the service the cgroup belongs to. peinit
advances it when a service's tree is leaked, so that the next run gets a
fresh tree; it is the number in a path's `%gen` suffix. Not the same
counter as `object.service.generation`, which advances on every start.

**Carried by:**

No event carries this field yet.

## <a id="object.cgroup.path"></a>`object.cgroup.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The cgroup the event is about, as its full path under
`/sys/fs/cgroup/peinit`. A service's cgroup is named for the service,
with any byte outside letters, digits, `.`, `_` and `-` written as `%`
and two hexadecimal digits, so the path can differ from the service name.
Once a service's tree has leaked, later trees carry a `%gen` suffix and
the cgroup generation, so that a new run never shares a tree with an
unkillable process. A submitted job's cgroup is under `jobs/`, named by
the job's GUID.

**Carried by:**

No event carries this field yet.

## <a id="object.cgroup.type"></a>`object.cgroup.type`

- **Type:** `str.enum`
- **Values:** `service-tree` · `health` · `hooks` · `helper`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Which part of a service's process containment the cgroup is.
`service-tree` is the whole of it and the most serious to lose; `health`
and `hooks` hold its health checks and hooks; `helper` is a pre-start
check helper's cgroup.

**Carried by:**

No event carries this field yet.

## <a id="object.claim.holder"></a>`object.claim.holder`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The package that holds `object.claim.role` after the event, by name.
Absent when the event left the role unheld, as revoking a claim does.

**Carried by:**

No event carries this field yet.

## <a id="object.claim.role"></a>`object.claim.role`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The role a claim event changed the holder of. A role is a virtual name
that several installed packages may contend to own on the filesystem,
with at most one holding it at a time (PSPU §5.23).

**Carried by:**

No event carries this field yet.

## <a id="object.device.name"></a>`object.device.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The device a firmware blob was being loaded for.

**Not emitted today.** The firmware check runs in the hook on the file
read, which sees the file and not the device that requested it, so the
kernel has no device to report.

**Carried by:**

No event carries this field yet.

## <a id="object.event-namespace.pattern"></a>`object.event-namespace.pattern`

- **Type:** `str`
- **Asserted:** yes
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The event-namespace pattern whose security descriptor eventd checked a
caller's access against. It is the pattern the descriptor was written for,
not the event type the caller asked about: eventd looks for a descriptor
under the event type itself, then under each shorter dotted prefix of it,
then under `*`, and uses the first it finds. A read of
`kacs.audit.access.checked` therefore records `kacs` or `*` when that is
where the descriptor lives, so a search for one event type by its full name
misses checks made under a broader pattern.

The value is eventd's claim, copied by the kernel from the check's audit
context, so a record carrying it also carries `fields.attestation.userspace`.

**Carried by:**

No event carries this field yet.

## <a id="object.fd-store.name"></a>`object.fd-store.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The name a service gave a file descriptor it asked peinit to keep, with
`FDNAME=`. A descriptor sent without a name is stored as `stored`.
Names are not unique: a service may store several descriptors under one
name, and two services may use the same one, so a name identifies
nothing on its own without `object.service.name`.

**Carried by:**

No event carries this field yet.

## <a id="object.file.code-kind"></a>`object.file.code-kind`

- **Type:** `str.enum`
- **Values:** `exec-image` · `mapped-library` · `firmware-blob`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What kind of code load the record concerns: an image being executed, a
library being mapped executable, or a firmware blob being loaded for a
device. A search on `object.file.path` returns all three; this tells them
apart.

**Carried by:**

No event carries this field yet.

## <a id="object.file.delete-on-close-count"></a>`object.file.delete-on-close-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many delete-on-close requests are armed on the file's inode. The file
is removed when the last handle carrying one is closed, so a count above
zero on an open says the file is already scheduled to disappear.

**Carried by:**

No event carries this field yet.

## <a id="object.file.digest"></a>`object.file.digest`

- **Type:** `bin`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The SHA-256 digest of a file whose signature was checked. The strongest
identifier of "this exact binary" a record can carry: unlike a path or an
inode it survives a rename and changes when the content does.

**Carried by:**

No event carries this field yet.

## <a id="object.file.elf-type"></a>`object.file.elf-type`

- **Type:** `str.enum`
- **Values:** `none` · `rel` · `exec` · `dyn` · `core`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The ELF type of an executable, from `e_type`, with the `ET_` prefix removed
and the name folded to lower case. `exec` is a fixed-address executable,
`dyn` a position-independent one or a shared object. The PIE mitigation
refuses `exec`. Open because the ELF standard reserves ranges for
operating-system and processor-specific types.

**Carried by:**

No event carries this field yet.

## <a id="object.file.fs-type"></a>`object.file.fs-type`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The type of filesystem the file lives on, by name, such as `ext4`. Mount
policy is derived from the filesystem type, so this explains why a file on
`proc` was never checked at all.

**Carried by:**

No event carries this field yet.

## <a id="object.file.gid"></a>`object.file.gid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux GID that owns the file, as `stat` reports it. Like
`object.file.uid`, a projection rather than anything KACS decides on.

**Carried by:**

No event carries this field yet.

## <a id="object.file.inode"></a>`object.file.inode`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The inode number the object presents. The best object identifier a
filesystem record has, and **neither stable nor unique**: StrataFS builds a
private inode for every open that shares the number of the outer one, a
mount root's number follows whichever stratum provides it, and numbers are
re-derived at mount time. Expect both false joins and false splits when
correlating on it.

**Carried by:**

No event carries this field yet.

## <a id="object.file.inode-lower"></a>`object.file.inode-lower`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The inode number of the real object in the underlying filesystem, beneath
a stacking filesystem's own. Stable, but unique only within that
filesystem. Carried beside `object.file.inode`; the two differing is how a
record shows that the object a caller holds has been rebound to a different
backing object.

**Carried by:**

No event carries this field yet.

## <a id="object.file.inode-replacement"></a>`object.file.inode-replacement`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The inode number of the object that took this one's place: the new object
in a supersede, or the object found where the expected one should have
been. A record carrying both this and `object.file.inode` names the
object that was meant and the object that was there.

**Carried by:**

No event carries this field yet.

## <a id="object.file.integrity"></a>`object.file.integrity`

- **Type:** `uint.integrity`
- **Values:** `0 Untrusted` · `4096 Low` · `8192 Medium` · `12288 High` · `16384 System`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mandatory integrity label on the file, as an integrity RID. Distinct
from any principal's integrity: a record about lowering a file's label
carries both, and `subject.token.integrity` is the caller's.

**Carried by:**

No event carries this field yet.

## <a id="object.file.integrity-capped"></a>`object.file.integrity-capped`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the label an exec would have taken from the file's signature was
capped at the process's current label instead of applied. The kernel does
this when a traced process, or one running with `no_new_privs`, execs a
binary whose signature would raise its PIP label: the exec goes ahead, but
a tracer that no longer dominated the process must not keep control of it.
True means the binary ran with less trust than its signing key grants.

The label capped is the PIP label, `object.process.pip.type` and
`object.process.pip.trust`, despite the field's name.

**Carried by:**

No event carries this field yet.

## <a id="object.file.mode"></a>`object.file.mode`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The object's POSIX permission bits, as `stat` reports them in the low
twelve bits of `st_mode`: the read, write and execute triples, set-user-ID,
set-group-ID and sticky. A projection for Linux compatibility; access is
decided by the security descriptor, never by these bits. The object's type
is `object.file.type`, not the high bits of this field.

**Carried by:**

No event carries this field yet.

## <a id="object.file.mount-owner.cookie"></a>`object.file.mount-owner.cookie`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount that owns an on-disk staging object, where that is not the mount
inspecting it. Two mounts can share a create stratum, so a mount recovering
orphans can meet another mount's staging; this, against
`object.file.mount.cookie`, is the ownership check that decides whether the
object is left alone.

**Carried by:**

No event carries this field yet.

## <a id="object.file.mount.cookie"></a>`object.file.mount.cookie`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount instance the file lives on, as the 64-bit random cookie StrataFS
assigns each mount. Two mounts sharing a stratum produce otherwise
indistinguishable records, which only this separates.

**Not emitted today.** Only the StrataFS ftrace tracepoints carry the
cookie; no event does yet.

**Carried by:**

No event carries this field yet.

## <a id="object.file.parent.inode"></a>`object.file.parent.inode`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The inode number of the directory that holds the file. Subject to the same
caveats as `object.file.inode`: neither stable nor unique.

**Carried by:**

No event carries this field yet.

## <a id="object.file.parent.path"></a>`object.file.parent.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The path of the directory that holds the file the operation acted on.
Carried where the parent is what was decided on — creating or removing an
entry is authorised against the directory, not the entry.

**Carried by:**

No event carries this field yet.

## <a id="object.file.path"></a>`object.file.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The absolute path of the file the operation acted on, resolved at the
enforcement point.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected)

## <a id="object.file.path-relative"></a>`object.file.path-relative`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The path of the object within its mount, `/`-prefixed. **Not an absolute
system path** — deliberately a separate field from `object.file.path`,
because a search for an absolute path would otherwise match KACS records
and silently miss these.

StrataFS events fire from inside the filesystem, below the layer where a
mount is known, so there is no absolute path for them to resolve against.
The KACS events covering the same operation do carry the caller's absolute
path, joined by the header's `emitter.process.guid` and time.

An absolute path to the **backing** object is derivable from this record
alone: join this onto `destination.stratum.path` for a copy-up, or onto
`source.stratum.path` for a refusal. That join is unavailable on a refusal
raised before any provider was determined, where the stratum path is
absent.

**Carried by:**

- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)
- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="object.file.size"></a>`object.file.size`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The size of the object in bytes or, on a copy, how many bytes the copy
moved. Distinguishes a copy-up of a large file from one of a symlink, which
otherwise produce the same record.

**Carried by:**

No event carries this field yet.

## <a id="object.file.size-previous"></a>`object.file.size-previous`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The size first observed, where the record compares it against a later one.
On a signature check this is the size when probing began and
`object.file.size` the size when it ended: a difference means the file was
written to while its signature was being read.

**Carried by:**

No event carries this field yet.

## <a id="object.file.tcb-signed"></a>`object.file.tcb-signed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the executed binary was signed by a key trusted at the TCB tier,
the floor for code that runs with full system trust. A usermodehelper exec
below the floor is refused; an ordinary exec below it is allowed, at the
lower trust its signature earns.

**Carried by:**

No event carries this field yet.

## <a id="object.file.type"></a>`object.file.type`

- **Type:** `str.enum`
- **Values:** `directory` · `regular` · `symlink` · `device` · `fifo` · `socket`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What kind of filesystem object the file is. Some operations are refused by
type alone — StrataFS will not copy a socket, FIFO or device up into a
writable stratum — and a copy-up of a directory moves no contents, so the
type is needed to read the rest of the record.

`device` covers both character and block devices.

**Carried by:**

No event carries this field yet.

## <a id="object.file.type-previous"></a>`object.file.type-previous`

- **Type:** `str.enum`
- **Values:** `directory` · `regular` · `symlink` · `device` · `fifo` · `socket`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The type the object had before it changed, beside `object.file.type`. The
pair records an object replaced by one of a different kind under the same
name, such as a stratum root that was a directory and is now a file.

**Carried by:**

No event carries this field yet.

## <a id="object.file.uid"></a>`object.file.uid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux UID that owns the file, as `stat` reports it. A copy-up preserves
the provider's owner, so this is the UID a disk quota is charged to,
whoever caused the copy. Ownership for access control is the descriptor's
owner SID, `object.sd.owner`.

**Carried by:**

No event carries this field yet.

## <a id="object.handle.enforced"></a>`object.handle.enforced`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the handle, or the object behind it, is under KACS enforcement.
False on a handle to an object on an unmanaged mount, where no descriptor
is checked and every later operation through the handle is allowed.

**Carried by:**

No event carries this field yet.

## <a id="object.handle.mode"></a>`object.handle.mode`

- **Type:** `uint.flags`
- **Values:** `0x1 FMODE_READ` · `0x2 FMODE_WRITE` · `0x4 FMODE_LSEEK` · `0x8 FMODE_PREAD` · `0x10 FMODE_PWRITE` · `0x20 FMODE_EXEC`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The kernel's open-mode bits on the file handle (`f_mode`). Only the bits
listed are stable meanings; the kernel sets others for its own
bookkeeping, and a consumer should ignore them. Distinct from
`access.granted`, which is what KACS allowed the handle; this is what the
handle was opened for.

**Carried by:**

No event carries this field yet.

## <a id="object.handle.origin-readable"></a>`object.handle.origin-readable`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether reading the StrataFS layer-origin attribute through the handle was
permitted when its view of the directory was settled. Decided once, at
open, and enforced at a much later call, so a refusal names a decision
made earlier than the record that reports it.

**Carried by:**

No event carries this field yet.

## <a id="object.hive.name"></a>`object.hive.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The name of the registry hive an operation acted on, such as `Machine` or
`Users`. A hive is the unit a registry source registers to serve, so this
names which source's namespace the operation reached.

**Carried by:**

No event carries this field yet.

## <a id="object.ipc.id"></a>`object.ipc.id`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The System V IPC identifier of the object, as `semget`, `shmget` or
`msgget` returned it. Small, reused once the object is removed, and scoped
to an IPC namespace, so it identifies an object only briefly and only
within one namespace.

**Carried by:**

No event carries this field yet.

## <a id="object.ipc.type"></a>`object.ipc.type`

- **Type:** `str.enum`
- **Values:** `sem` · `shm` · `msg`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which kind of System V IPC object the operation acted on: a semaphore set,
a shared-memory segment or a message queue.

**Carried by:**

No event carries this field yet.

## <a id="object.job.activation-generation"></a>`object.job.activation-generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The activation generation of the service the job belongs to, at the time
the job was created. The same counter as `object.service.generation`, so
it tells which run of a service a job served. Absent for a `submitted`
job, which belongs to no service; peinit holds zero for one today, which
must not be carried.

**Carried by:**

No event carries this field yet.

## <a id="object.job.arguments"></a>`object.job.arguments`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The job's argument vector, including `argv[0]`. Kept whole up to 32 KiB
of encoded arguments; past that, the arguments are cut at the last whole
argument that fits, never inside one, and `object.job.arguments-truncated`
is true. A cut argument vector is a prefix of the real one, so do not
read its last element as the last argument the job was given.

**Carried by:**

No event carries this field yet.

## <a id="object.job.arguments-count"></a>`object.job.arguments-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How many arguments the job was given, before any were cut. Equal to the
length of `object.job.arguments` unless that was cut.

**Carried by:**

No event carries this field yet.

## <a id="object.job.arguments-truncated"></a>`object.job.arguments-truncated`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Whether `object.job.arguments` was cut to fit the record. When true,
`object.job.arguments-count` says how many arguments there really were.

**Carried by:**

No event carries this field yet.

## <a id="object.job.created-time"></a>`object.job.created-time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

When peinit created the job, in nanoseconds since the Unix epoch.
Creation is when peinit decided to run it, before its process exists.

**peinit does not yet write this value.** It records creation today as
`created_at_ns`, read from the monotonic clock, which counts from boot
and is not comparable with any time in the record header. It must be
converted to realtime before it is carried under this field.

**Carried by:**

No event carries this field yet.

## <a id="object.job.duration"></a>`object.job.duration`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How long the job lasted, in nanoseconds, from its creation to its end.
**Measured from creation, not from start**, so it includes any time spent
waiting to start; subtract `object.job.created-time` from
`object.job.started-time` to find that part.

**Carried by:**

No event carries this field yet.

## <a id="object.job.executable"></a>`object.job.executable`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The path of the executable the job runs.

**Carried by:**

No event carries this field yet.

## <a id="object.job.guid"></a>`object.job.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The job the event is about. A job is one process peinit runs: a service's
main process, one of its hooks or health checks, or a job a client
submitted. The GUID is a UUIDv7, so it also orders jobs by when they were
created. peinit writes it today as UUID text, which must be converted.

**Carried by:**

No event carries this field yet.

## <a id="object.job.started-time"></a>`object.job.started-time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

When the job's process started, in nanoseconds since the Unix epoch.
Absent if the job never started, which is how a job that failed before
its process existed shows itself.

**peinit does not yet write this value.** It records the start today as
`started_at_ns`, read from the monotonic clock, as for
`object.job.created-time`.

**Carried by:**

No event carries this field yet.

## <a id="object.job.state"></a>`object.job.state`

- **Type:** `str.enum`
- **Values:** `created` · `running` · `completed` · `failed` · `abandoned`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The job's state after the event. `completed`, `failed` and `abandoned`
are terminal. `abandoned` means its process survived SIGKILL: the job is
over but the process is still there.

**Carried by:**

No event carries this field yet.

## <a id="object.job.submitter.sid"></a>`object.job.submitter.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The user SID of the client that submitted the job. Present only on a
`submitted` job. peinit writes it today as an SDDL string, which is not
this field's form and must be converted.

**Carried by:**

No event carries this field yet.

## <a id="object.job.token.groups"></a>`object.job.token.groups`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The group SIDs of the token the job's process runs as. peinit writes them
today as SDDL strings, which must be converted.

**Carried by:**

No event carries this field yet.

## <a id="object.job.token.privileges"></a>`object.job.token.privileges`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The privileges present on the token the job's process runs as, as the
flags of the 64-bit privilege word of `uapi/pkm/token.h`, one
`KACS_SE_*_PRIVILEGE` bit each. Present is not enabled: read
`object.job.token.privileges-enabled` for which ones the process can use
without enabling them first.

peinit writes privilege names today, not these flags, and must convert
them.

**Carried by:**

No event carries this field yet.

## <a id="object.job.token.privileges-enabled"></a>`object.job.token.privileges-enabled`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Which of the privileges in `object.job.token.privileges` are enabled, as
flags in the same 64-bit word. Always a subset of it.

peinit writes privilege names today, not these flags, and must convert
them.

**Carried by:**

No event carries this field yet.

## <a id="object.job.token.sid"></a>`object.job.token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The user SID of the token the job's process runs as. peinit writes it
today as an SDDL string, which must be converted.

**Carried by:**

No event carries this field yet.

## <a id="object.job.type"></a>`object.job.type`

- **Type:** `str.enum`
- **Values:** `service-main` · `pre-exec-hook` · `post-exec-hook` · `reload-hook` · `health-check` · `submitted`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

What the job is for. Every type except `submitted` belongs to a service,
named in `object.service.name`; a `submitted` job belongs to the client
that submitted it, named in `object.job.submitter.sid`, and has no
service.

**Carried by:**

No event carries this field yet.

## <a id="object.key.created"></a>`object.key.created`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a create-key request made a new key. False means the key already
existed and the request opened it instead, so the security descriptor and
volatility the caller asked for were **not** applied: the key keeps the
ones it already had.

**Carried by:**

No event carries this field yet.

## <a id="object.key.cross-source"></a>`object.key.cross-source`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a registry lookup crossed from one source's hive into another's by
following a symbolic link. When true, the key reached is served by a
different backend from the one the path began in.

**Carried by:**

No event carries this field yet.

## <a id="object.key.guid"></a>`object.key.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry key an operation acted on. Keys are identified by GUID rather
than by path, so a record names the key durably but not legibly — nothing
in the event stream currently binds a key GUID to the path an administrator
would recognise.

`key` means a registry key and nothing else. A cryptographic key is a
`signing-key`.

**Carried by:**

- [`lcs.audit.backup.ended`](~peios/events/lcs/lcs-audit-backup-ended)
- [`lcs.audit.backup.started`](~peios/events/lcs/lcs-audit-backup-started)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)
- [`lcs.audit.restore.ended`](~peios/events/lcs/lcs-audit-restore-ended)
- [`lcs.audit.restore.started`](~peios/events/lcs/lcs-audit-restore-started)
- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)

## <a id="object.key.layer.name"></a>`object.key.layer.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of the registry layer a key operation resolved in: the layer
whose entry the operation read or wrote. Distinct from `object.layer.name`,
which names a layer the operation acted on as a whole.

**Carried by:**

No event carries this field yet.

## <a id="object.key.parent.volatile"></a>`object.key.parent.volatile`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the parent of a key being created is volatile. A volatile key may
not have a non-volatile child, so a create that asks for a non-volatile key
beneath a volatile parent is refused.

**Carried by:**

No event carries this field yet.

## <a id="object.key.path"></a>`object.key.path`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The resolved absolute path of the registry key, in canonical form, such as
`Machine\System\KMES`. Carried beside `object.key.guid` so a record is
legible as well as durable. Resolved: a `%CURRENT_USER%` substitution has
already been made, and the path as the caller wrote it is
`object.key.path-requested`.

**Carried by:**

No event carries this field yet.

## <a id="object.key.path-requested"></a>`object.key.path-requested`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry path as the caller wrote it, before LCS rewrote it. A path
whose first component is the alias `CurrentUser` is rewritten to the
caller's own key under `Users`, named by the caller's SID; this field keeps
the original, and `object.key.path` holds the rewritten path.

The same requested path therefore names different keys for different
callers. Search on `object.key.path` to find which key was actually
reached.

**Carried by:**

No event carries this field yet.

## <a id="object.key.reference-count"></a>`object.key.reference-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The number of references held on a key's entry in the kernel's key cache,
at the moment of the record. Each open handle holds one, so a count that
reaches zero is the point at which LCS tells the source it may drop the
key.

**Carried by:**

No event carries this field yet.

## <a id="object.key.symlink"></a>`object.key.symlink`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a registry key is a symbolic link to another key. A lookup that
passes through a link key is redirected to its target, named by
`object.key.target.guid`.

**Carried by:**

No event carries this field yet.

## <a id="object.key.symlink-depth"></a>`object.key.symlink-depth`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many registry symbolic links a lookup followed before stopping. The
walk is bounded by the configured symlink depth limit, so a value at that
limit means the lookup was refused for following too many links.

**Carried by:**

No event carries this field yet.

## <a id="object.key.target.guid"></a>`object.key.target.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The key a registry symbolic link redirects to, by GUID. Necessarily
separate from `object.key.guid`: a record of a link being followed names
the link and its target at once.

**Carried by:**

No event carries this field yet.

## <a id="object.key.target.rsi.slot"></a>`object.key.target.rsi.slot`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The registry source slot that owns the target of a symbolic link, present
when it differs from the source that owns the link itself. A link that
leads into another source's hive is the registry's equivalent of a
filesystem symlink crossing a trust boundary; see `object.key.cross-source`.

**Carried by:**

No event carries this field yet.

## <a id="object.key.value.digest"></a>`object.key.value.digest`

- **Type:** `bin`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A digest of a registry value's data, so that two records can be compared
to see whether a value changed without either carrying the data.
Recorded in place of the raw bytes, which an event never carries by
default. Compare digests only with digests: the algorithm is not yet
fixed.

**Carried by:**

No event carries this field yet.

## <a id="object.key.value.length"></a>`object.key.value.length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The byte length of a registry value's data. Recorded in place of the data
itself, which an event never carries by default because values can be
large and can hold secrets.

**Carried by:**

No event carries this field yet.

## <a id="object.key.value.name"></a>`object.key.value.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of the registry value an operation acted on. The empty string is
a legal name, identifying the key's default value, so an empty field and
an absent one mean different things: absent means the record concerns no
value at all.

**Carried by:**

No event carries this field yet.

## <a id="object.key.value.type"></a>`object.key.value.type`

- **Type:** `uint.enum`
- **Values:** `0 REG_NONE` · `1 REG_SZ` · `2 REG_EXPAND_SZ` · `3 REG_BINARY` · `4 REG_DWORD` · `5 REG_DWORD_BIG_ENDIAN` · `6 REG_LINK` · `7 REG_MULTI_SZ` · `8 REG_RESOURCE_LIST` · `9 REG_FULL_RESOURCE_DESCRIPTOR` · `10 REG_RESOURCE_REQUIREMENTS_LIST` · `11 REG_QWORD` · `65535 REG_TOMBSTONE`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The type of a registry value, as the number of its `REG_*` constant.
`REG_TOMBSTONE` is LCS's own marker for a value deleted within one layer:
it hides the value from lower layers rather than holding data, and appears
only on a write that deletes.

**Carried by:**

No event carries this field yet.

## <a id="object.key.volatile"></a>`object.key.volatile`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a registry key is volatile, meaning it lives only in memory and
does not survive a reboot.

**Carried by:**

No event carries this field yet.

## <a id="object.key.volatile-requested"></a>`object.key.volatile-requested`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The volatility a create-key caller asked for. It can differ from
`object.key.volatile` when the request opened an existing key, whose
volatility a create request does not change.

**Carried by:**

No event carries this field yet.

## <a id="object.kind"></a>`object.kind`

- **Type:** `str.enum`
- **Values:** `file` · `process` · `token` · `key` · `socket` · `ipc` · `event-namespace` · `metric-namespace` · `log-namespace` · `eventd-admin`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What sort of thing the operation acted on. Load-bearing rather than
descriptive: it names the table an access mask in the same record decodes
against, and without it `access.granted` has no defined meaning.

The mask spaces genuinely collide. `0x0001` is `FILE_READ_DATA` on a file
and `PROCESS_TERMINATE` on a process; the socket mapping reuses
`FILE_WRITE_DATA` as a socket's write right.

`event-namespace`, `metric-namespace`, `log-namespace` and `eventd-admin`
come from eventd's audit context, on access checks eventd asks KACS to make
against its own descriptors. The first three are checks against a
namespace pattern; `eventd-admin` is eventd's check of whether a caller may
administer it, the `administer()` check in eventd's `query/security.rs`.

`socket` and `ipc` have no identity fields yet. A record carrying either
kind names the object only by its kind, until those enforcement points are
plumbed to supply one.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.handle.used`](~peios/events/kacs/kacs-audit-handle-used)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)
- [`kacs.descriptor.rejected`](~peios/events/kacs/kacs-descriptor-rejected)
- [`lcs.audit.key.opened`](~peios/events/lcs/lcs-audit-key-opened)

## <a id="object.layer.base"></a>`object.layer.base`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether an operation targeted the base layer, the bottom of every key's
resolution order. The base layer always exists at precedence 0 and cannot
be disabled.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.enabled"></a>`object.layer.enabled`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether a registry layer is enabled, after the change the record
describes. A disabled layer takes no part in resolution: its values exist
but no reader sees them.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.enabled-previous"></a>`object.layer.enabled-previous`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether a registry layer was enabled before the change the record
describes. Read with `object.layer.enabled`: a record where the two differ
is a layer being switched on or off.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.name"></a>`object.layer.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The name of the registry layer an operation acted on, as written when the
layer was created. Layer names are compared without regard to case, so
two records whose names differ only in case name the same layer. The base
layer is named `base`.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.precedence"></a>`object.layer.precedence`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

A registry layer's precedence, after the change the record describes.
Where two layers define the same value, the one with the higher
precedence wins, and the higher sequence breaks a tie. This number
therefore decides which value the whole system sees.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.precedence-previous"></a>`object.layer.precedence-previous`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

A registry layer's precedence before the change the record describes.
Read with `object.layer.precedence`: raising a layer above another
silently changes which of their values every reader resolves.

**Carried by:**

No event carries this field yet.

## <a id="object.layer.resolution-changed"></a>`object.layer.resolution-changed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether a change to a layer altered what any reader of the registry
actually resolves, as opposed to changing a layer whose values were
already outranked. LCS computes this and discards it today, so it is not
yet emitted on any record.

**Carried by:**

No event carries this field yet.

## <a id="object.log-namespace.pattern"></a>`object.log-namespace.pattern`

- **Type:** `str`
- **Asserted:** yes
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The log-store namespace pattern whose security descriptor eventd checked a
caller's access against. As with `object.event-namespace.pattern`, it is the
pattern the descriptor was written for, not the log origin the caller asked
about: eventd tries the origin, then each shorter dotted prefix, then `*`,
and uses the first that has a descriptor.

An origin may name a producer within a service after a `/`, such as
`jobs/<guid>`, and that part is never a pattern: the walk starts at the
service. A service's hooks, reloads and health checks therefore record the
service's own pattern, and a search for the full origin finds none of them.

The value is eventd's claim, copied by the kernel from the check's audit
context, so a record carrying it also carries `fields.attestation.userspace`.

**Carried by:**

No event carries this field yet.

## <a id="object.metric-namespace.pattern"></a>`object.metric-namespace.pattern`

- **Type:** `str`
- **Asserted:** yes
- **Carried in:** the payload
- **Defined in:** `eventd.evman`

The metric-namespace pattern whose security descriptor eventd checked a
caller's access against. As with `object.event-namespace.pattern`, it is the
pattern the descriptor was written for, not the metric name: eventd tries the
name, then each shorter dotted prefix, then `*`, and uses the first that has
a descriptor.

eventd checks metric namespaces for two different things, reading stored
metrics and publishing a sample, and this field is the same for both. Which
one was checked is in `access.requested`, not here.

The value is eventd's claim, copied by the kernel from the check's audit
context, so a record carrying it also carries `fields.attestation.userspace`.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.cookie"></a>`object.mount.cookie`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount instance the operation acted on, as the 64-bit random cookie
StrataFS assigns each mount.

**Not emitted today.** Only the StrataFS ftrace tracepoints carry the
cookie, and no superblock identifier exists for other filesystems: their
tracepoints carry the superblock's magic number, which names a filesystem
type rather than an instance.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.cookie-epoch"></a>`object.mount.cookie-epoch`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The boot a mount cookie belongs to. A cookie read back from an on-disk
marker can name a live mount only if it was written in this boot, and this
is what decides that.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.depth"></a>`object.mount.depth`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The filesystem stacking depth of a StrataFS mount: one more than the
deepest stacking filesystem among its strata. Linux permits a depth of at
most 2, so a mount whose strata are themselves stacked filesystems can be
refused with `ELOOP`.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.fs-type"></a>`object.mount.fs-type`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The type of filesystem mounted, by name, such as `ext4` or `tmpfs`. Mount
policy is derived from it: the kernel decides from the type alone that a
`proc` or `sysfs` mount is unmanaged.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.options"></a>`object.mount.options`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The stack option string of a StrataFS mount exactly as the caller supplied
it, whether or not it could be parsed. That is what makes it useful on a
rejected mount: it shows what was asked for, where `object.mount.strata`
could only show what was understood.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.options-previous"></a>`object.mount.options-previous`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The stack option string a StrataFS mount was created with, recorded on a
remount beside the string the remount supplied in `object.mount.options`.
A remount may not change the stack, and the test is a byte-for-byte
comparison of the two strings, so a stack that is equivalent but written
differently is refused.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.path"></a>`object.mount.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The directory the mount was attached at, as an absolute path.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.policy"></a>`object.mount.policy`

- **Type:** `str.enum`
- **Values:** `unmanaged` · `deny-missing` · `synthesize-ephemeral` · `synthesize-persistent`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The KACS mount policy in force, which decides what happens to an object
with no stored descriptor. `unmanaged` means **no access control at all**:
every check on the mount is skipped. `deny-missing` refuses access to an
object without a descriptor. The two `synthesize` policies build one from
the parent and the mount's template, and differ in whether it is written
back to disk.

Changing a mount from `deny-missing` to a `synthesize` policy with a chosen
template makes the template's author the author of every unlabelled
object's access control on that volume.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.policy-generation"></a>`object.mount.policy-generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount-policy generation in force. Every policy change increments it,
and every descriptor cached under an older generation is then stale, so a
change invalidates the cached descriptors of a whole volume at once.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.policy-requested"></a>`object.mount.policy-requested`

- **Type:** `str.enum`
- **Values:** `unmanaged` · `deny-missing` · `synthesize-ephemeral` · `synthesize-persistent`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount policy a caller asked for, beside `object.mount.policy`. On a
refused change, the policy that stayed in force and the one that was
wanted.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.root"></a>`object.mount.root`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The filesystem root that was captured when the mount was made, and against
which every later layer path is resolved. Fixed for the life of the mount,
so a mounter in a chroot binds the mount to that chroot's view of the
filesystem for good.

**Carried by:**

No event carries this field yet.

## <a id="object.mount.strata"></a>`object.mount.strata`

- **Type:** `str.path[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The configured stack of strata of a StrataFS mount, as an ordered list of
directory paths. Index 0 is the highest-precedence stratum: where several
strata hold the same name, the one with the lowest index provides it. At
most 16 entries. Each entry's position is the index that
`source.stratum.index` and its relatives refer to.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.duration"></a>`object.operation.duration`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How long the operation lasted, in nanoseconds, from when it was requested
to when it ended. **Measured from the request, not from when it started
running**, so it includes any time it spent pending behind other work.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.guid"></a>`object.operation.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The peinit operation the event is about: a start, stop, restart, reload
or reset of one service, from the moment it is requested to the moment
it ends. The GUID is a UUIDv7. peinit writes it today as UUID text,
which must be converted.

**Not the generic `operation` domain.** `operation.name` and its
siblings describe what any event attempted; `object.operation` is a
thing peinit manages, and a search for one does not find the other.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.merged-into.guid"></a>`object.operation.merged-into.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The operation that absorbed this one. A merged operation's work is done,
or not, by the operation named here, so follow it to learn the outcome.
peinit writes it today as UUID text, which must be converted.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.source"></a>`object.operation.source`

- **Type:** `str.enum`
- **Values:** `admin` · `boot` · `shutdown` · `dependency-propagation` · `restart-policy` · `timer` · `binds-to-recovery` · `binds-to-propagation` · `conflict-resolution` · `on-failure` · `tty-release`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Who or what asked for the operation. `admin` is the only source a
client's command produces; every other source is peinit acting for its
own reasons. An `admin` operation is the one to tie to a person, through
the access check that admitted the command.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.state"></a>`object.operation.state`

- **Type:** `str.enum`
- **Values:** `pending` · `running` · `completed` · `failed` · `merged` · `cancelled` · `aborted`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The operation's state after the event. `completed`, `failed`, `merged`,
`cancelled` and `aborted` are terminal. `cancelled` means it ended while
still pending and never ran; `aborted` means it ended while running;
`merged` means another operation absorbed it, named in
`object.operation.merged-into.guid`.

**Carried by:**

No event carries this field yet.

## <a id="object.operation.type"></a>`object.operation.type`

- **Type:** `str.enum`
- **Values:** `start` · `stop` · `restart` · `reload` · `reset`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

What the operation does to its service.

**Carried by:**

No event carries this field yet.

## <a id="object.package.architectures"></a>`object.package.architectures`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The architecture of each package in `object.package.names`, at the same
index: an identifier of PSPU §5.8, such as `x86_64`, `aarch64` or
`noarch`. `noarch` is a real architecture, meaning the package runs on
any of them, and is not the absence of one.

A package being removed has no architecture in the transaction's plan.
peipkg writes an empty string for one today, which this field's
definition does not admit, and how a removal is represented here is not
yet settled.

**Carried by:**

No event carries this field yet.

## <a id="object.package.name"></a>`object.package.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The name of the package the event is about, on an event that concerns
one package. A package's name is its identity across every repository
that serves it (PSPU §5.3), so the same package from two repositories
has the same value here; `object.package.repositories` says which one an
install drew from.

An event that concerns several packages, such as a transaction, carries
`object.package.names` instead.

**Carried by:**

No event carries this field yet.

## <a id="object.package.names"></a>`object.package.names`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The names of the packages a transaction touched, one per package it
installed, upgraded, downgraded or removed. The arrays
`object.package.versions`, `object.package.versions-previous`,
`object.package.architectures` and `object.package.repositories` are
parallel to this one: the element at an index describes the package at
the same index here.

A failed transaction that was rolled back still lists the packages it
would have touched. Whether anything changed is the event's outcome,
not this list.

**Carried by:**

No event carries this field yet.

## <a id="object.package.repositories"></a>`object.package.repositories`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The repository each package in `object.package.names` was installed from,
at the same index, by the name it is configured under. One transaction
can draw from several repositories, which is why this is per package
rather than per event. It is how a bad install is traced back to the
repository that served it.

**A package with no repository has three causes**, and none is a missing
value: a removal has no source, a package installed from a local file
had no repository, and an orphaned package's repository is no longer
configured. peipkg writes an empty string for all three today, which
this field's definition does not admit; read the event type to tell
them apart until that is settled.

**Carried by:**

No event carries this field yet.

## <a id="object.package.versions"></a>`object.package.versions`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The version of each package in `object.package.names`, at the same index:
the version installed, or, for a package the transaction removed, the
version removed. A removal and an install of the same version look the
same here; the event type and outcome tell them apart.

**Carried by:**

No event carries this field yet.

## <a id="object.package.versions-previous"></a>`object.package.versions-previous`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The version each package in `object.package.names` replaced, at the same
index, on an upgrade or downgrade. Read beside `object.package.versions`
to see which way a package moved: comparing the two by PSPU §5.6 tells
an upgrade from a downgrade.

**peipkg does not emit this value today.** A package the transaction
installed fresh or removed replaced no version, and how such a package is
represented in a parallel array is not yet settled.

**Carried by:**

No event carries this field yet.

## <a id="object.process.core-dump"></a>`object.process.core-dump`

- **Type:** `str.enum`
- **Values:** `disable` · `user` · `root`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the process may dump core, as Linux's dumpable setting: `disable`
forbids a dump, `user` dumps as the process's user, and `root` dumps
readable only by root. The kernel forces `disable` on a PIP-protected
process at exec, because a core file is a copy of the memory the protection
exists to keep private.

**Carried by:**

No event carries this field yet.

## <a id="object.process.core-dump-previous"></a>`object.process.core-dump-previous`

- **Type:** `str.enum`
- **Values:** `disable` · `user` · `root`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The core-dump setting before the operation changed it. The pair is the
whole content of a record that hardens a process at exec.

**Carried by:**

No event carries this field yet.

## <a id="object.process.executable"></a>`object.process.executable`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The executable of the process the operation acted on, resolved at exec with
symbolic links followed.

**Carried by:**

No event carries this field yet.

## <a id="object.process.exit-code"></a>`object.process.exit-code`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The exit code of the job's process, as it passed it to `exit`. Present
only when the process exited of its own accord; a process ended by a
signal has `object.process.exit-signal` instead, and never both.

A non-zero code is not necessarily a failure, because a definition may
name other codes as success. Whether the job failed is
`object.job.state`.

**Carried by:**

No event carries this field yet.

## <a id="object.process.exit-signal"></a>`object.process.exit-signal`

- **Type:** `int`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The number of the signal that ended the job's process. Present only when
a signal ended it; a process that exited has `object.process.exit-code`
instead, and never both. A signal peinit sent to stop the job, such as
SIGTERM or SIGKILL, appears here like any other.

**Carried by:**

No event carries this field yet.

## <a id="object.process.guid"></a>`object.process.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the process the operation acted on. Distinct from
`emitter.process.guid` — one record carries both when a process opens
another process.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

## <a id="object.process.mitigations"></a>`object.process.mitigations`

- **Type:** `uint.flags`
- **Values:** `0x1 WXP` · `0x2 TLP` · `0x4 LSV` · `0x8 CFI` · `0x10 UI_ACCESS` · `0x20 NO_CHILD` · `0x40 CFIF` · `0x80 CFIB` · `0x100 PIE` · `0x200 SML`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The process mitigations in force after the operation, from
`uapi/pkm/psb.h`. Applying mitigations only ever adds bits to the set.
`CFI` is a legacy alias for `CFIF` and `CFIB` together and is never set in
this field, and `UI_ACCESS` is reserved.

**Carried by:**

No event carries this field yet.

## <a id="object.process.mitigations-added"></a>`object.process.mitigations-added`

- **Type:** `uint.flags`
- **Values:** `0x1 WXP` · `0x2 TLP` · `0x4 LSV` · `0x8 CFI` · `0x10 UI_ACCESS` · `0x20 NO_CHILD` · `0x40 CFIF` · `0x80 CFIB` · `0x100 PIE` · `0x200 SML`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The bits this operation newly turned on. Requesting a mitigation already
in force is not an error, so this can be empty on a successful request.

**Carried by:**

No event carries this field yet.

## <a id="object.process.mitigations-normalised"></a>`object.process.mitigations-normalised`

- **Type:** `uint.flags`
- **Values:** `0x1 WXP` · `0x2 TLP` · `0x4 LSV` · `0x8 CFI` · `0x10 UI_ACCESS` · `0x20 NO_CHILD` · `0x40 CFIF` · `0x80 CFIB` · `0x100 PIE` · `0x200 SML`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The request after the kernel normalised it: the `CFI` alias replaced by
`CFIF` and `CFIB`. A request naming an unknown bit, or a CFI half the CPU
does not support, fails normalisation and is refused outright.

**Carried by:**

No event carries this field yet.

## <a id="object.process.mitigations-requested"></a>`object.process.mitigations-requested`

- **Type:** `uint.flags`
- **Values:** `0x1 WXP` · `0x2 TLP` · `0x4 LSV` · `0x8 CFI` · `0x10 UI_ACCESS` · `0x20 NO_CHILD` · `0x40 CFIF` · `0x80 CFIB` · `0x100 PIE` · `0x200 SML`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mitigations the caller asked for, as written. Compare against
`object.process.mitigations-normalised` to see how the kernel read the
request.

**Carried by:**

No event carries this field yet.

## <a id="object.process.name"></a>`object.process.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The kernel's name (`comm`) for the process the operation acted on. Lossy
and truncated to 15 bytes; two processes can share a name.

**Carried by:**

No event carries this field yet.

## <a id="object.process.parent.guid"></a>`object.process.parent.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the parent of a newly created process. Correlate on
this rather than `object.process.parent.pid`.

**Carried by:**

No event carries this field yet.

## <a id="object.process.parent.pid"></a>`object.process.parent.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The process ID of the parent of a newly created process. A fork record is
written by the process that called `fork` or `clone`, so this usually
equals `emitter.process.pid`; it differs under `CLONE_PARENT`, which makes
the child a sibling of its creator.

**Carried by:**

No event carries this field yet.

## <a id="object.process.pid"></a>`object.process.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The process ID of the process the operation acted on. As with
`emitter.process.pid`, correlate durably on the GUID instead.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

## <a id="object.process.pip.trust"></a>`object.process.pip.trust`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The PIP trust level of the process the operation acted on. Compared against
the caller's `subject.pip.trust` for dominance: a caller whose trust does
not dominate this is denied before the DACL is reached.

**Carried by:**

No event carries this field yet.

## <a id="object.process.pip.type"></a>`object.process.pip.type`

- **Type:** `uint.enum`
- **Values:** `0 None` · `512 Protected` · `1024 Isolated`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Protected Isolated Process type of the process the operation acted on.
Compared against the caller's `subject.pip.type` for dominance, so a record
carrying both shows which side of the boundary each stood on.

**Carried by:**

No event carries this field yet.

## <a id="object.process.shares-security"></a>`object.process.shares-security`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a newly created task shares its creator's security state rather
than receiving its own copy. True for a new thread (`CLONE_THREAD`), which
shares one process state and therefore one process GUID; false for a fork,
which gets a new process state and a new GUID.

**Carried by:**

No event carries this field yet.

## <a id="object.process.threads"></a>`object.process.threads`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many threads the process had when the operation ran. Read with
`object.process.threads-switched`.

**Carried by:**

No event carries this field yet.

## <a id="object.process.threads-switched"></a>`object.process.threads-switched`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many of the process's threads took on a new identity in the operation.
A primary token install applies to every thread; a value below
`object.process.threads` means some threads still run under the old token,
a process split between two identities.

**Carried by:**

No event carries this field yet.

## <a id="object.process.token-previous.guid"></a>`object.process.token-previous.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the primary token a token install displaced. With
`object.process.token.guid`, the before and after of the process's identity.

**Carried by:**

No event carries this field yet.

## <a id="object.process.token-previous.sid"></a>`object.process.token-previous.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The user SID of the token a token install displaced. Comparing it against
the new token's SID is how a record shows a process changing which
principal it runs as, rather than only replacing its token.

**Carried by:**

No event carries this field yet.

## <a id="object.process.token.guid"></a>`object.process.token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the primary token the process holds after the
operation. Carried on a token install, where it names the token the process
now runs as; the token it replaced is `object.process.token-previous.guid`.

**Carried by:**

No event carries this field yet.

## <a id="object.repository.name"></a>`object.repository.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The repository the event is about, by the name it is configured under.
The name is local configuration, not an identity: a repository is
identified by its base URL, in `object.repository.url`, and two systems
may call one repository by different names.

**Carried by:**

No event carries this field yet.

## <a id="object.repository.url"></a>`object.repository.url`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peipkg.evman`

The base URL of the repository the event is about, which is what
identifies it (PSPU §5.36). An HTTPS URL unless the repository was
given an insecure-transport allowance, so an `http:` value here marks a
repository whose indexes are fetched without transport security.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.cache-state"></a>`object.sd.cache-state`

- **Type:** `str.enum`
- **Values:** `valid` · `missing` · `corrupt`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The state of the descriptor KACS holds cached for the inode. Anything but
`valid` means the normal check could not run against the object's own
descriptor; what happened instead depends on the mount policy, and a
caller with `SeRestorePrivilege` can replace a missing or corrupt one
outright.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.components"></a>`object.sd.components`

- **Type:** `uint.flags`
- **Values:** `0x1 OWNER` · `0x2 GROUP` · `0x4 DACL` · `0x8 SACL` · `0x10 LABEL`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which parts of the descriptor the operation addressed, as the
`KACS_SECINFO_*` bits of `uapi/pkm/sd.h`. Each part is guarded by a
different right — `WRITE_OWNER` for the owner, `WRITE_DAC` for the DACL,
`ACCESS_SYSTEM_SECURITY` for the SACL — so a record about a descriptor
change is read with this.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.digest"></a>`object.sd.digest`

- **Type:** `bin`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A digest of the object's security descriptor in its binary form, so that
two records can be compared for "same descriptor" without either carrying
the descriptor itself.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.digest-previous"></a>`object.sd.digest-previous`

- **Type:** `bin`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The digest of the descriptor a change replaced. Equal to `object.sd.digest`
on a change that rewrote the descriptor without altering it.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.length"></a>`object.sd.length`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The byte length of the object's security descriptor. Where a record names
two descriptors, this is the object's own.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.length-previous"></a>`object.sd.length-previous`

- **Type:** `uint.bytes`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The byte length of the descriptor a change replaced.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.mount-generation"></a>`object.sd.mount-generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The mount-policy generation stamped on the cached descriptor when it was
cached. Compared with `object.mount.policy-generation`: a descriptor from an
older generation is stale and is discarded on next use.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.owner"></a>`object.sd.owner`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The owner SID on the object's security descriptor. Not the token's default
owner, `object.token.default-owner`, which is the owner a token gives the
objects it creates.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.owner-previous"></a>`object.sd.owner-previous`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The owner SID a change replaced. Taking ownership is how a principal gains
the right to rewrite an object's DACL, so the pair is the record of who
lost control of the object to whom.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.provenance"></a>`object.sd.provenance`

- **Type:** `str.enum`
- **Values:** `xattr` · `missing` · `synthetic` · `synthetic-pending` · `corrupt` · `stratafs-root`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Where the cached descriptor came from. `xattr` was read from the object's
stored descriptor; `synthetic` was built from the parent and the mount's
template; `synthetic-pending` was synthesised on a persistent mount and has
not yet been written back; `stratafs-root` is a StrataFS root's descriptor,
read through the outer inode and re-read on every check. A different
vocabulary from `object.sd.cache-state`, held beside it on the same entry.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.synthesis-depth"></a>`object.sd.synthesis-depth`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many ancestor directories a descriptor synthesis walked. An object
with no stored descriptor inherits from its parent, which may itself need
synthesising, so the walk climbs until it finds a labelled ancestor.

**Carried by:**

No event carries this field yet.

## <a id="object.sd.synthesis-depth-limit"></a>`object.sd.synthesis-depth-limit`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The ceiling on `object.sd.synthesis-depth`, 32 levels in this kernel. A
synthesis that reaches it fails closed: no descriptor is built and the
access is refused, however the object's ancestors are labelled.

**Carried by:**

No event carries this field yet.

## <a id="object.service.conflict.name"></a>`object.service.conflict.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The name of the service this one conflicts with, on a finding that two
services both triggered at boot declare a conflict and so cannot both
start. Which of the pair is `object.service.name` and which is this field
carries no meaning: the conflict is mutual.

**Carried by:**

No event carries this field yet.

## <a id="object.service.dependency.kind"></a>`object.service.dependency.kind`

- **Type:** `str.enum`
- **Values:** `requires` · `wants` · `binds-to`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How the service depends on `object.service.dependency.name`. `requires`
and `binds-to` are hard: the service cannot start without the dependency.
`binds-to` is also tied to it afterwards, and stops and recovers with it.

**Carried by:**

No event carries this field yet.

## <a id="object.service.dependency.name"></a>`object.service.dependency.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The name of the dependency a graph finding is about: the service this
one requires and cannot have, or the one whose block has blocked it.
Read `object.service.dependency.kind` for how this service depends on it.

The name is as the definition wrote it. A missing-dependency finding
names a service that does not exist, so do not expect to find any other
record about it.

**Carried by:**

No event carries this field yet.

## <a id="object.service.dependents"></a>`object.service.dependents`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The services that hard-depend on this one, by name. Hard dependencies are
`requires` and `binds-to`; a `wants` dependent is not listed, because it
starts whether or not this service does.

**Carried by:**

No event carries this field yet.

## <a id="object.service.failed"></a>`object.service.failed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Whether an internal error in peinit failed the service it occurred on.
False means peinit contained the error without changing the service's
state. Either way the fault was peinit's, not the service's.

**Carried by:**

No event carries this field yet.

## <a id="object.service.generation"></a>`object.service.generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The service's activation generation: a counter peinit advances each time
the service enters `starting`, so that every incarnation of a service has
its own number. Records with the same `object.service.name` and the same
generation describe one run of the service.

The same counter as `object.job.activation-generation`, seen from the
service rather than from one of its jobs. It is held in memory and starts
again when peinit does, so it orders runs within one boot only.

**Carried by:**

No event carries this field yet.

## <a id="object.service.health-check.interval"></a>`object.service.health-check.interval`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The configured interval between health checks, in nanoseconds. Configured
in whole seconds, so it is always a whole number of seconds.

**Carried by:**

No event carries this field yet.

## <a id="object.service.health-check.restart-window"></a>`object.service.health-check.restart-window`

- **Type:** `uint.duration`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The configured restart window of a health check, in nanoseconds.
Configured in whole seconds, so it is always a whole number of seconds.
A validation finding carries it beside `object.service.health-check.interval`
and `object.service.health-check.retries`, because it is their
combination that a definition gets wrong.

**Carried by:**

No event carries this field yet.

## <a id="object.service.health-check.retries"></a>`object.service.health-check.retries`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The configured number of consecutive health-check failures at which
peinit stops reporting the service unhealthy and acts on it. Failures
short of this count change nothing but the service's health.

**Carried by:**

No event carries this field yet.

## <a id="object.service.name"></a>`object.service.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The name of the service the event is about, as its definition names it.
The same value peinit passes as the object name in the KACS audit context
when it checks a caller's access to a service, so a peinit record and the
access-check record for the same command join on it.

A name, not a durable identity: a service removed and later redefined
under the same name is a different service with the same
`object.service.name`. Read `object.service.generation` beside it to tell
one activation from the next.

**Carried by:**

No event carries this field yet.

## <a id="object.service.on-failure-chain"></a>`object.service.on-failure-chain`

- **Type:** `str[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The OnFailure handlers already started in the chain that peinit cut
short, in the order they were started. A chain is cut when the next
handler is already in it, which is a loop, or when it has reached sixteen
handlers.

**Carried by:**

No event carries this field yet.

## <a id="object.service.on-failure.name"></a>`object.service.on-failure.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The OnFailure handler peinit declined to start, because starting it would
have looped or gone too deep. The failure the handler was meant to handle
went unhandled, so look for it here when a handler did not run.

**Carried by:**

No event carries this field yet.

## <a id="object.service.state"></a>`object.service.state`

- **Type:** `str.enum`
- **Values:** `inactive` · `starting` · `active` · `reloading` · `stopping` · `completed` · `backoff` · `failed` · `abandoned` · `skipped`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The service's state after the event, in the vocabulary of the control
channel (PSPU §4.B). Exactly four states satisfy dependents: `active`,
`reloading`, `completed` and `skipped`. Use that set and no other when
asking whether something depending on this service could be running.

`abandoned` means a process survived SIGKILL and is still there,
unkillably. It is not a stopped service.

**Carried by:**

No event carries this field yet.

## <a id="object.service.state-previous"></a>`object.service.state-previous`

- **Type:** `str.enum`
- **Values:** `inactive` · `starting` · `active` · `reloading` · `stopping` · `completed` · `backoff` · `failed` · `abandoned` · `skipped`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The service's state before the event, with the same values as
`object.service.state`. The two together are the transition; a record
carrying only one of them says where the service is, not how it got
there.

**Carried by:**

No event carries this field yet.

## <a id="object.service.timer.schedule"></a>`object.service.timer.schedule`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

The service's timer schedule, exactly as its definition wrote it. On a
finding that the schedule does not parse, this is the text that failed,
so it may not be a valid schedule at all.

**Carried by:**

No event carries this field yet.

## <a id="object.service.transition-cause"></a>`object.service.transition-cause`

- **Type:** `str.enum`
- **Values:** `explicit-start` · `dependency-start` · `restart-policy` · `binds-to-recovery` · `timer` · `explicit-stop` · `explicit-reload` · `explicit-reset` · `conflict-eviction` · `binds-to-propagation` · `shutdown-wave` · `process-crash` · `clean-exit` · `clean-exit-restart` · `readiness-timeout` · `watchdog-timeout` · `health-check-failure` · `pre-hook-failure` · `parent-setup-failure` · `pre-exec-failure` · `dependency-failure` · `restart-budget-exhausted` · `cycle-detected` · `validation-error` · `assertion-error` · `condition-skipped` · `tty-unavailable` · `process-unkillable` · `internal-error`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

Why the service's state changed. The causes beginning `explicit-` follow
an operator's command; the rest are peinit's own reasons, and an operator
reading one has learned what the manager did, not what anyone asked for.

**`internal-error` is a fault in peinit, not in the service.** The
service was failed because peinit could not carry out a step on its
behalf; the service itself may have been healthy.

**Carried by:**

No event carries this field yet.

## <a id="object.service.type"></a>`object.service.type`

- **Type:** `str.enum`
- **Values:** `simple` · `oneshot`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How the service's main process is supervised. A `simple` service is up
while its process runs; a `oneshot` service runs to completion and is
then `completed`. Health checks are scheduled for `simple` services only,
which is why a validation finding names the type.

**Carried by:**

No event carries this field yet.

## <a id="object.session.auth-package"></a>`object.session.auth-package`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of the authentication package that established the session, as
the creator supplied it. Not interpreted by the kernel.

**Carried by:**

- [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed)

## <a id="object.session.id"></a>`object.session.id`

- **Type:** `uint.luid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The LUID of the logon session the operation acted on. The same value as
`subject.token.auth-id` and `object.token.auth-id` on records about tokens
in that session, which is how a session's records are joined to everything
done under it.

**Carried by:**

- [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed)

## <a id="object.session.logon-time"></a>`object.session.logon-time`

- **Type:** `uint.time`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

When the session was established.

**Carried by:**

- [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed)

## <a id="object.session.logon-type"></a>`object.session.logon-type`

- **Type:** `str.enum`
- **Values:** `interactive` · `network` · `batch` · `service` · `network-cleartext` · `new-credentials` · `remote-interactive`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What kind of logon the session represents, from the `KACS_LOGON_TYPE_*`
values in `uapi/pkm/token.h`. The kernel refuses to create a session of any
other type.

**Carried by:**

- [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed)

## <a id="object.session.reference-count"></a>`object.session.reference-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many live tokens or other references the session still holds. A
session is destroyed when this reaches zero; on a refused destroy, a
non-zero count is why.

**Carried by:**

No event carries this field yet.

## <a id="object.session.sid"></a>`object.session.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The logon SID the kernel synthesised for the session. Derived from
`object.session.id`, but it appears in descriptors as a principal in its own
right, so a search by SID has to find it here.

**Carried by:**

No event carries this field yet.

## <a id="object.session.user.sid"></a>`object.session.user.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The user SID of the principal the logon session belongs to: whose session
it is. Not `object.session.sid`, which is the logon SID synthesised for the
session itself; a search for what one user's sessions did matches this
field, and a search for one session matches that one.

**Carried by:**

- [`kacs.session.destroyed`](~peios/events/kacs/kacs-session-destroyed)

## <a id="object.socket.address"></a>`object.socket.address`

- **Type:** `str.ip`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The address a listening socket is bound to. A wildcard address (`0.0.0.0`
or `::`) is a legitimate value: it means every address on the machine.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.id"></a>`object.socket.id`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The identity of the socket the operation acted on.

**Not emitted today.** Peios publishes no stable socket identifier; the
kernel's inode number and pointer are both unsuitable, so records name a
socket only by its kind and, for a listener, its address and port.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.identity-dropped"></a>`object.socket.identity-dropped`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether a conveyed identity was dropped because the receiver's control
buffer was too small to hold it. The message is delivered either way, so
true means the receiver got data with no identity attached and could not
tell.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.impersonation-limit"></a>`object.socket.impersonation-limit`

- **Type:** `uint.enum`
- **Values:** `0 Anonymous` · `1 Identification` · `2 Impersonation` · `3 Delegation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The highest impersonation level the socket will convey to a peer.
Raising it to `Impersonation` or `Delegation` lets a receiver act as the
sender, not merely identify it.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.options"></a>`object.socket.options`

- **Type:** `uint.flags`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The options of a listening socket: whether it is one of an `SO_REUSEPORT`
group, whether an IPv6 socket refuses IPv4-mapped traffic, and whether a
bound UDP socket is also connected to one peer. The kernel reports these
today as three separate booleans, and no bit assignment for them is
defined yet.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.port"></a>`object.socket.port`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The port a listening socket is bound to. A listener has one port, which is
neither a source nor a destination, so it is not `source.port` or
`destination.port`; a search for a port number should cover all three.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.principal-kind"></a>`object.socket.principal-kind`

- **Type:** `str.enum`
- **Values:** `unstamped` · `program` · `kernel`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

What kind of principal governs the socket for network policy. `program` is
a process, whose token and process facts were stamped on the socket;
`kernel` is a kernel socket, with no token. `unstamped` is a socket that
was never stamped, so network policy has nobody to attribute its traffic
to.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.reservation"></a>`object.socket.reservation`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The port-reservation selector a bind matched, naming the reservation whose
descriptor decided whether the caller could bind the port. Peios replaces
the privileged-port floor with these reservations entirely, so this is the
rule that let a process listen on its port.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.state"></a>`object.socket.state`

- **Type:** `str.enum`
- **Values:** `free` · `unconnected` · `connecting` · `connected` · `disconnecting`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The socket's connection state, from the Linux `SS_*` value with its prefix
removed and folded to lower case. A listening socket reads `unconnected`
here: listening is a transport state, not a connection state.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.token-delivered"></a>`object.socket.token-delivered`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the conveyed token actually reached the receiver. False means the
message arrived and the identity did not.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.token-derived"></a>`object.socket.token-derived`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the token conveyed on a send was derived from the sender's token
rather than passed as is, so the receiver did not get the sender's token
itself.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.token-passing"></a>`object.socket.token-passing`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether automatic per-send token passing is on for the socket: whether
every send carries the sender's identity to the receiver without being
asked.

**Carried by:**

No event carries this field yet.

## <a id="object.socket.type"></a>`object.socket.type`

- **Type:** `str.enum`
- **Values:** `stream` · `dgram` · `raw` · `rdm` · `seqpacket`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The socket's type, from the Linux `SOCK_*` value with its prefix removed
and folded to lower case.

**Carried by:**

No event carries this field yet.

## <a id="object.thread.tid"></a>`object.thread.tid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

A thread the operation acted on, where it is not the emitting thread:
the target of a per-thread impersonation or of a thread-token open.

**Carried by:**

No event carries this field yet.

## <a id="object.token.auth-id"></a>`object.token.auth-id`

- **Type:** `uint.luid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The LUID of the logon session the token the operation acted on belongs to.
The same value as `object.session.id` on that session's own records.

**Carried by:**

No event carries this field yet.

## <a id="object.token.capabilities"></a>`object.token.capabilities`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The confinement capability SIDs (`S-1-15-3-…`) of the token the operation
acted on. Unrelated to Linux capabilities.

**Carried by:**

No event carries this field yet.

## <a id="object.token.default-owner"></a>`object.token.default-owner`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The owner SID the token stamps on objects it creates. Changing it changes
who owns everything the token makes from then on, which is why a default
adjustment is worth a record.

**Carried by:**

No event carries this field yet.

## <a id="object.token.elevation"></a>`object.token.elevation`

- **Type:** `str.enum`
- **Values:** `default` · `full` · `limited`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The token's role in a split elevation pair. `full` is the elevated half
and `limited` the filtered one; `default` is a token that belongs to no
pair. The other half of a pair is `object.token.linked.guid`.

**Carried by:**

No event carries this field yet.

## <a id="object.token.gid"></a>`object.token.gid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux GID the token the operation acted on projects onto.

**Carried by:**

No event carries this field yet.

## <a id="object.token.group-attributes"></a>`object.token.group-attributes`

- **Type:** `uint.flags[]`
- **Values:** `SE_GROUP_MANDATORY` · `SE_GROUP_ENABLED_BY_DEFAULT` · `SE_GROUP_ENABLED` · `SE_GROUP_OWNER` · `SE_GROUP_USE_FOR_DENY_ONLY` · `SE_GROUP_INTEGRITY` · `SE_GROUP_INTEGRITY_ENABLED` · `SE_GROUP_RESOURCE` · `SE_GROUP_LOGON_ID`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Per-group attribute bitmasks of the token the operation acted on,
positionally parallel to `object.token.groups`: `groups[i]` is described by
`group-attributes[i]`. A group adjustment changes these and not the SIDs,
so a record of one is read here.

**Carried by:**

No event carries this field yet.

## <a id="object.token.groups"></a>`object.token.groups`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The group SIDs of the token the operation acted on. Read with
`object.token.group-attributes`, which says which of them are enabled.

**Carried by:**

No event carries this field yet.

## <a id="object.token.guid"></a>`object.token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the token the operation acted on. Distinct from
`emitter.token.guid` — one record carries both when a token is used to
open or adjust another token.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

## <a id="object.token.id"></a>`object.token.id`

- **Type:** `uint.luid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The LUID of the token the operation acted on, for token-open and
token-adjust checks.

**Carried by:**

- [`kacs.audit.access.checked`](~peios/events/kacs/kacs-audit-access-checked)
- [`kacs.audit.privilege.used`](~peios/events/kacs/kacs-audit-privilege-used)
- [`kacs.caap.sacl.skipped`](~peios/events/kacs/kacs-caap-sacl-skipped)
- [`kacs.caap.staging.diverged`](~peios/events/kacs/kacs-caap-staging-diverged)

## <a id="object.token.impersonation"></a>`object.token.impersonation`

- **Type:** `uint.enum`
- **Values:** `0 Anonymous` · `1 Identification` · `2 Impersonation` · `3 Delegation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The impersonation level of the token the operation acted on. A primary
token reports 0, so read `object.token.type` before reading 0 as
Anonymous.

**Carried by:**

No event carries this field yet.

## <a id="object.token.impersonation-permitted"></a>`object.token.impersonation-permitted`

- **Type:** `uint.enum`
- **Values:** `0 Anonymous` · `1 Identification` · `2 Impersonation` · `3 Delegation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The impersonation level a gate computed as permitted. Where it is below
`object.token.impersonation`, the level was silently reduced: the caller
lacked the privilege to impersonate at the full level, or the client's
integrity was higher than the caller's. The operation still succeeds, at
the lower level.

**Carried by:**

No event carries this field yet.

## <a id="object.token.integrity"></a>`object.token.integrity`

- **Type:** `uint.integrity`
- **Values:** `0 Untrusted` · `4096 Low` · `8192 Medium` · `12288 High` · `16384 System`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The integrity level of the token the operation acted on, as an integrity
RID.

**Carried by:**

No event carries this field yet.

## <a id="object.token.interactive-session"></a>`object.token.interactive-session`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The interactive-session scope the token is bound to, which separates the
interactive sessions of one machine from each other. 0 means the token is
bound to no interactive session.

**Carried by:**

No event carries this field yet.

## <a id="object.token.linked.guid"></a>`object.token.linked.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the other token in a linked elevation pair. Carried
where two tokens are linked, so the record names both halves.

**Carried by:**

No event carries this field yet.

## <a id="object.token.primary-group"></a>`object.token.primary-group`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The primary-group SID the token stamps on objects it creates, beside
`object.token.default-owner`.

**Carried by:**

No event carries this field yet.

## <a id="object.token.privileges"></a>`object.token.privileges`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The privileges the token the operation acted on holds, as the flags of its
64-bit privilege word: bit n is the privilege whose LUID is n.

**Carried by:**

No event carries this field yet.

## <a id="object.token.privileges-enabled"></a>`object.token.privileges-enabled`

- **Type:** `uint.flags`
- **Values:** `0x4 KACS_SE_CREATE_TOKEN_PRIVILEGE` · `0x8 KACS_SE_ASSIGN_PRIMARY_TOKEN_PRIVILEGE` · `0x10 KACS_SE_LOCK_MEMORY_PRIVILEGE` · `0x20 KACS_SE_INCREASE_QUOTA_PRIVILEGE` · `0x80 KACS_SE_TCB_PRIVILEGE` · `0x100 KACS_SE_SECURITY_PRIVILEGE` · `0x200 KACS_SE_TAKE_OWNERSHIP_PRIVILEGE` · `0x400 KACS_SE_LOAD_DRIVER_PRIVILEGE` · `0x800 KACS_SE_SYSTEM_PROFILE_PRIVILEGE` · `0x1000 KACS_SE_SYSTEMTIME_PRIVILEGE` · `0x2000 KACS_SE_PROFILE_SINGLE_PROCESS_PRIVILEGE` · `0x4000 KACS_SE_INCREASE_BASE_PRIORITY_PRIVILEGE` · `0x20000 KACS_SE_BACKUP_PRIVILEGE` · `0x40000 KACS_SE_RESTORE_PRIVILEGE` · `0x80000 KACS_SE_SHUTDOWN_PRIVILEGE` · `0x100000 KACS_SE_DEBUG_PRIVILEGE` · `0x200000 KACS_SE_AUDIT_PRIVILEGE` · `0x800000 KACS_SE_CHANGE_NOTIFY_PRIVILEGE` · `0x1000000 KACS_SE_REMOTE_SHUTDOWN_PRIVILEGE` · `0x10000000 KACS_SE_MANAGE_VOLUME_PRIVILEGE` · `0x20000000 KACS_SE_IMPERSONATE_PRIVILEGE` · `0x100000000 KACS_SE_RELABEL_PRIVILEGE` · `0x800000000 KACS_SE_CREATE_SYMBOLIC_LINK_PRIVILEGE`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Which of the privileges in `object.token.privileges` are enabled, as flags
in the same bit layout. A privilege adjustment changes this, not the held set.

**Carried by:**

No event carries this field yet.

## <a id="object.token.restricted"></a>`object.token.restricted`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the token is restricted: whether it carries restricting SIDs that
every access check must also satisfy.

**Carried by:**

No event carries this field yet.

## <a id="object.token.restricting-sids"></a>`object.token.restricting-sids`

- **Type:** `bin.sid[]`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The restricting SIDs on a filtered token: the second list an access check
must also satisfy before a restricted token is granted anything. Carried
where a token is filtered, or where a filtered token is acted on.

**Carried by:**

No event carries this field yet.

## <a id="object.token.sid"></a>`object.token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The user SID of the token the operation acted on. On a record where one
principal handles another's token — duplicating, filtering or installing
it — this is the principal the token speaks for, and `subject.token.sid`
the one who handled it.

**Carried by:**

No event carries this field yet.

## <a id="object.token.supplementary-gid-count"></a>`object.token.supplementary-gid-count`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

How many supplementary GIDs the token's Linux projection carries. A token
naming more groups than Linux can hold fails projection with `-E2BIG`, and
this is the count that was too many.

**Carried by:**

No event carries this field yet.

## <a id="object.token.type"></a>`object.token.type`

- **Type:** `str.enum`
- **Values:** `primary` · `impersonation`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the token the operation acted on is a primary token or an
impersonation token. As with `subject.token.type`, needed to read
`object.token.impersonation`: a primary token also reports 0 there.

**Carried by:**

No event carries this field yet.

## <a id="object.token.uid"></a>`object.token.uid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The Linux UID the token the operation acted on projects onto. A projection
for interoperability, never the identity KACS decides on.

**Carried by:**

No event carries this field yet.

## <a id="object.token.user-deny-only"></a>`object.token.user-deny-only`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the token's user SID is deny-only: it matches deny ACEs but never
allow ACEs, so the token gets nothing through its own user identity.

**Carried by:**

No event carries this field yet.

## <a id="object.token.write-restricted"></a>`object.token.write-restricted`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

Whether the token is write-restricted: its restricting SIDs apply only to
write access, and reads are decided as for an unrestricted token.

**Carried by:**

No event carries this field yet.

## <a id="object.watch.depth-limit"></a>`object.watch.depth-limit`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The maximum depth beneath its key at which a subtree watch reports
changes. 0 means unbounded, and 0 is the default. The limit is the
machine-wide `MaxSubtreeWatchDepth` setting rather than anything the
watcher chose, so changes deeper than it are suppressed for every subtree
watch at once.

**Carried by:**

No event carries this field yet.

## <a id="object.watch.effects"></a>`object.watch.effects`

- **Type:** `uint.flags`
- **Values:** `0x1 layer-delete`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The internal effects that a registry commit triggered through the
kernel's own configuration watches. `layer-delete` means the watch
dispatch for the commit already handled a layer deletion, so the commit
skips its own separate layer-delete step. Absent when the commit
triggered none.

**Carried by:**

No event carries this field yet.

## <a id="object.watch.event"></a>`object.watch.event`

- **Type:** `str.enum`
- **Values:** `value-set` · `value-deleted` · `subkey-created` · `subkey-deleted` · `sd-changed` · `key-deleted` · `overflow`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The type of a registry watch event, named from its `REG_WATCH_*` constant
with the prefix removed. `overflow` replaces individual events when they
could not all be delivered, telling the watcher only that it missed
something and must re-read the key.

An `overflow` does not always mean a full queue. It is also queued when a
single event could not be encoded, so a watcher seeing one cannot tell
which happened.

**Carried by:**

No event carries this field yet.

## <a id="object.watch.filter"></a>`object.watch.filter`

- **Type:** `uint.flags`
- **Values:** `0x1 REG_NOTIFY_VALUE` · `0x2 REG_NOTIFY_SUBKEY` · `0x4 REG_NOTIFY_SD`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The categories of change a process asked a registry watch to report: value
changes, subkey creation and deletion, and security descriptor changes. A
watcher is told only of changes in the categories it set.

**Carried by:**

No event carries this field yet.

## <a id="object.watch.subtree"></a>`object.watch.subtree`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Whether a registry watch covers the whole subtree beneath its key rather
than the key alone. How deep a subtree watch reaches is
`object.watch.depth-limit`, and that limit is unbounded by default.

**Carried by:**

No event carries this field yet.

## <a id="object.xattr.name"></a>`object.xattr.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The name of an extended attribute the operation acted on, in full with its
namespace prefix, such as `security.capability`. The names Peios reserves
for its own descriptors and markers are refused or hidden whatever the
caller's access.

**Carried by:**

No event carries this field yet.

*Generated from `eventd.evman`, `kernel.evman`, `lcs.evman`, `peinit.evman`, `peipkg.evman`, `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
