---
title: Phase 1
description: The compiled-in phase with no registry dependency, whose whole purpose is to reach the point where a registry can serve.
---

Phase 1 is compiled into peinit. It does not change at runtime and has
no registry dependency, because its whole purpose is to reach the point
where a registry exists. It does the minimum needed to make Phase 2
possible, and most of its failures are fatal to the boot.

## Step 1: Confirm the root is writable

The initramfs delivers the root mounted read-write. peinit does not
remount it — mount flags belong to the initramfs, and a redundant
remount of an already-writable or overlay root can fail for reasons that
have nothing to do with the root being usable.

Instead peinit probes. It creates `/.peinit/` if it is absent, writes a
uniquely named file there — the name is derived from peinit's own PID
and a namespace identifier, so two probes cannot collide — writes to it,
and removes it. If any part of that fails, the root is not usable for
Phase 2 and peinit enters recovery mode.

## Step 2: Mount what is missing

`/proc`, `/sys` and `/dev` are already mounted. peinit does not
blindly mount them again: a redundant mount stacks a second filesystem
over the populated one, and on some kernel and flag combinations returns
`EBUSY` instead.

peinit reads `/proc/self/mountinfo` to find out what is already there,
and mounts only what is not:

| Mount point | Filesystem | Flags | Provided by |
|---|---|---|---|
| `/proc` | proc | nosuid, nodev, noexec | initramfs |
| `/sys` | sysfs | nosuid, nodev, noexec | initramfs |
| `/dev` | devtmpfs | nosuid | initramfs |
| `/dev/pts` | devpts | nosuid, noexec | peinit |
| `/dev/shm` | tmpfs | nosuid, nodev | peinit |
| `/run` | tmpfs | nosuid, nodev | peinit |
| `/sys/fs/cgroup` | cgroup2 | nosuid, nodev, noexec | peinit |

Each `mount(2)` passes the filesystem name as both the source and the
filesystem type, passes only the listed flags, and passes null mount
data. Mount points that do not exist are created first.

There is a bootstrap wrinkle in reading mountinfo at all: the file lives
in `/proc`, which is one of the things being checked for. If the read
fails with `ENOENT` or `ENOTDIR`, peinit mounts `/proc` from the table
and retries. Any other failure to read or parse mountinfo sends peinit
to recovery.

For the three initramfs-provided rows, an already-mounted filesystem is
success, and so is an `EBUSY` from an attempted mount. For the four
peinit owns, a mount failure sends peinit to recovery.

### Seeding descriptors on the new filesystems

Three of the four filesystems peinit mounts are fresh and empty:
`/dev/shm`, `/run` and `/sys/fs/cgroup`. Under KACS an inode with no
Security Descriptor is denied to every caller, and there is nothing on a
newly mounted tmpfs for a new inode to inherit from — so peinit stamps
the mount root with a descriptor that grants SYSTEM and Administrators
full control and is marked inheritable by both containers and objects:

```
O:SY G:SY D:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)
```

Everything created underneath — the notify socket, per-service runtime
directories, the cgroup hierarchy — inherits from it; the two sockets
that need a different population are stamped explicitly in step 9. This is why peinit never sets mode bits on the sockets it creates;
under KACS they would mean nothing, and the descriptor is the thing that
does the work. It is the same descriptor the initramfs seeds onto the
root filesystem, and the two are kept identical on purpose: this one
inheritable ACL is, in practice, the access policy of everything under
these mounts, so an ACE missing here is missing from every per-service
directory under `/run/services`.

Failure to apply the descriptor sends peinit to recovery. Without it
every file peinit later creates on that filesystem would be unreachable
to everything, including peinit.

`/proc`, `/sys` and `/dev` are not stamped: they arrive from the
initramfs already populated.

### Device node policy

`/dev` arrives with that same inheritable descriptor on its root and on
every node, which is the right default — whatever the root grants, a
disk hot-plugged later inherits, so the root must be acceptable on a raw
block device — but it leaves `/dev/null` unusable by anyone who is not
an administrator. A single inherited descriptor cannot say "`/dev/null`
for everyone, the disks for administrators", so peinit enumerates the
exceptions. Once the mounts are up it stamps each of these nodes with a
descriptor of its own:

| Node | DACL |
|---|---|
| `/dev/null`, `/dev/zero`, `/dev/full`, `/dev/random`, `/dev/urandom`, `/dev/tty`, `/dev/ptmx` | `D:(A;;GA;;;SY)(A;;GA;;;BA)(A;;FRFW;;;WD)` |

Everyone may open the node for reading and writing and may stat it;
nobody but SYSTEM and Administrators may change its descriptor. Only the
DACL is replaced — owner and group stay as the seed left them — and the
ACEs carry no inheritance flags, because a device node has no children.
`/dev/console` is deliberately not on the list: it is the SYSTEM
console.

The step is advisory. A node that cannot be stamped is reported as a
warning and stays on the inherited default, usable by administrators
and denied to everyone else; a node that does not exist is noted and
skipped. Neither sends peinit to recovery.

## Step 3: Restore the persisted random seed

peinit restores the seed at `/var/state/peinit/random-seed` once `/dev`
is available and before registryd starts. The seed is a machine-local
entropy cache for the kernel CSPRNG. It is not configuration, and
shipping one in a packaged image, live ISO or VM template would hand
every instance of that image the same starting entropy.

If the file is absent, that is an ordinary first boot or a stateless
live boot, and peinit continues silently. When a seed is present peinit
mixes it into the kernel pool, preferring the interface that credits
entropy for a locally persisted seed; if that fails it mixes the bytes
without crediting and records the failure. A seed file that is empty, or
larger than 4096 bytes, is treated as an error.

Nothing in this step can send peinit to recovery. A system with no
entropy cache still boots; it just starts with less entropy, which is a
problem for the image builder to solve with a hardware or virtio RNG
rather than with a seed baked into the image.

The initramfs may perform the same restore earlier, once the persistent
root is mounted. peinit's restore stays as the fallback for initramfs
images that do not participate and for boots that have no initramfs.

## Step 4: Ensure the local machine ID

`/lcl/etc/machine-id` holds a stable local install identifier used for
software compatibility, log correlation and instance identity. It is not
a security principal: not a credential, not a SID, not an account, and
not an input to any authorisation decision.

The format is 128 bits as exactly 32 lowercase hexadecimal characters
followed by one newline. A valid existing file is left alone. A file
that is absent, empty, all zeroes, the wrong length, not hexadecimal, or
missing its trailing newline is replaced: peinit draws 128 bits from the
kernel CSPRNG and writes a valid file atomically, through a temporary
file and a rename, with the result flushed.

Any failure of this step — an unreadable file, a CSPRNG failure, or an
unwritable path — sends peinit to recovery. The write does not create
parent directories, so an image that ships without `/lcl/etc/` present
fails here rather than at first use.

Images and templates are expected to ship with no machine ID, or with an
empty file as a reset marker. Clone tooling that wants a new identity
removes or truncates the file and lets the next boot generate one.
Stateless live boots without a persistent overlay get an ephemeral ID
for that boot.

## Step 5: Set the clock from the hardware RTC

peinit reads the hardware clock and calls `clock_settime()` before
registryd starts, so that timestamps on registry operations, log entries
and the boot attempt counter mean something.

It opens `/dev/rtc`, falling back to `/dev/rtc0` if that device is
absent, and reads it with `RTC_RD_TIME`. The returned `struct rtc_time`
is interpreted as UTC and converted to `CLOCK_REALTIME` seconds with
zero nanoseconds.

Every failure in this step sends peinit to recovery: no openable RTC
device, a failed read, a value that is invalid or before the Unix epoch,
a failed `clock_settime`, and — deliberately — a failure to close the
descriptor after a successful read. Leaking a descriptor in PID 1 during
bootstrap is a symptom of something being badly wrong, not a detail to
swallow.

> [!NOTE]
> NTP corrects the clock properly later in the boot. This step only gets
> it into the right decade, so that early timestamps are not absurd and
> the timer subsystem has a wall clock to anchor to.

## Step 6: Start registryd

peinit holds a compiled-in definition for registryd — the only compiled-in
service definition there is:

| Field | Value |
|---|---|
| ImagePath | `/sbin/registryd` |
| Arguments | `Machine=/var/state/loregd/Machine.hive`, `Users=/var/state/loregd/Users.hive` |
| Identity | `SYSTEM` |
| Readiness | Notify |
| ErrorControl | Critical |

The hive paths are peinit's choice, not registryd's: where the machine
registry lives is a boot-policy decision, and it is made here because
this is the one service start that cannot consult configuration.

peinit mints a SYSTEM token including registryd's per-service SID,
creates the cgroup tree, forks with the token installed, and execs
`/sbin/registryd` through the runtime StrataFS view. Two separate
timeouts bound the start, both 30 seconds: one on process setup, driven
synchronously because there is no event loop yet, and one on readiness.

registryd's `READY=1` means "accepting and serving registry requests",
not "the process is alive" — it does not signal until its storage
backend is open, its schema is validated and it can answer a read.

### The schema-version guard

After readiness, peinit ensures the base registry structure exists and
then probes it. Ensuring comes first: peinit creates `Machine\System`,
`Machine\System\Services` and `Machine\System\Init` if they are absent
and stamps `Machine\System\Services\SchemaVersion` with the current
schema version, 1. Only then does it read the value back.

The read is what verifies registryd is genuinely serving. A value that
is present but not a `REG_DWORD`, or that is a `REG_DWORD` of the wrong
length, fails the probe. A key or value that is absent reads as zero and
passes — the structure was just created, so absence at this point means
the write did not take effect, and the failure that matters is the
provisioning failure, which is reported directly.

The consequence is that the guard is self-healing. An unprovisioned
first boot, or a registry cleared by the recovery tools, comes up with
an empty `Machine\System\Services\` and boots into a Phase 2 with no
services rather than into recovery.

### Keeping registryd

When registryd passes readiness and the probe, peinit retains the
activation as an ordinary runtime service instance: its state, its
pidfd-tracked main process, its cgroup generation and paths, its output
pipe ownership, its notify generation, its job identity, and any cleanup
evidence. Ownership is not dropped at the Phase 2 boundary.

During Phase 2 the registry's own definition of `registryd`, if there is
one, is merged onto the retained activation. peinit does not create a
second inactive record and does not restart registryd because a
definition has appeared. If the registry definition is absent or
invalid, the ordinary graph validation rules apply.

If registryd fails to start, its readiness times out, or the probe
fails, peinit enters recovery. There is no Phase 2 without a registry.

## Step 7: Autorun scripts

Between registryd starting and path provisioning, peinit runs every
non-directory entry in `/lcl/policy/autorun.d`, in sorted order, by
absolute path, with the working directory `/` and `PATH=/sbin:/bin`.
Each runs under peinit's own SYSTEM token.

The step is fail-open at every point: a missing directory, an unreadable
directory, a spawn failure and a non-zero exit are all console warnings
and none of them stops the boot. Its console output bypasses the quiet
policy (§2.6), because a script that ran this early and went wrong needs
to be visible.

## Step 8: Provision boot-time paths

Covered in §2.4.

## Step 9: Infrastructure setup

Three things, before Phase 2 begins:

1. **The control socket** at `/run/services/peinit/control.sock`, which
   serves every runtime command for the lifetime of the system, stamped
   for SYSTEM and Administrators (§10.1).
2. **The jobs socket** at `/run/services/peinit/jobs.sock`, on which
   any authenticated principal may submit a job once Phase 2 runs,
   stamped so that connecting is the submission permission (§10.7).
3. **Loopback**: peinit brings up `lo` over netlink, because services
   that bind `127.0.0.1` need it.

Either socket failing to bind or to take its descriptor sends peinit to
recovery — without the first there is no way to administer the system,
and a jobs socket with the wrong descriptor is either unreachable or
open to everything. A loopback bring-up failure is a warning that lets
Phase 2 proceed.

## Failure summary

| Failure | Response |
|---|---|
| Root writability probe fails | Recovery |
| A mount point cannot be created | Recovery |
| A peinit-owned filesystem fails to mount | Recovery |
| A mounted filesystem cannot be stamped with its descriptor | Recovery |
| `/proc/self/mountinfo` unreadable or unparseable | Recovery |
| `/proc`, `/sys` or `/dev` already mounted, or `EBUSY` | Tolerated as success |
| A device node in the policy list cannot be stamped | Warning; node keeps the inherited default |
| A device node in the policy list does not exist | Noted; boot continues |
| Random seed absent, oversized, empty, or unrestorable | Warning; boot continues |
| Machine ID read, generation, or write fails | Recovery |
| Machine ID absent, empty, or malformed | Regenerated; boot continues |
| Any RTC or clock failure | Recovery |
| registryd fails to start, or setup times out | Recovery |
| registryd readiness times out | Recovery |
| Base registry provisioning fails | Recovery |
| Schema-version probe returns a wrong type or length | Recovery |
| An autorun script is missing, unspawnable, or exits non-zero | Warning; boot continues |
| A provisioning entry is malformed | Warning; entry skipped |
| An optional provisioned path fails | Warning; boot continues |
| A required provisioned path fails | Recovery |
| Control socket creation or stamping fails | Recovery |
| Jobs socket creation or stamping fails | Recovery |
| Loopback bring-up fails | Warning; boot continues |
