---
title: Bootstrap
---

peinit's boot has two phases: a hardcoded bootstrap that brings up
the minimum infrastructure, and a registry-driven phase that starts
everything else. The boundary between them is registryd. This
section defines Phase 1 and the identity model that governs early
boot.

## Initramfs contract

peinit assumes the root filesystem is fully assembled and mountable
when it starts. Root storage assembly -- LUKS decryption, LVM
activation, RAID array assembly, and any filesystem check -- is the
initramfs's responsibility, performed (if at all) before peinit
runs. peinit neither performs nor assumes a root fsck.

The initramfs transfers control to peinit as PID 1 by `chroot`-ing
into the assembled root and exec'ing peinit there -- not via
`switch_root`/`pivot_root`, because the kernel forbids relocating
onto the initramfs rootfs. Consequently the initramfs rootfs is not
gone: it remains the mount-namespace root (emptied and unreachable
from peinit's view). peinit MUST NOT assume a clean single-root
mount topology and MUST NOT attempt `pivot_root`.

peinit is installed at a fixed path on the real root
(`/usr/bin/peinit`); the boot-image tooling sets the kernel `init=`
command line to that path, which the initramfs honours when
transferring control.

At handoff the initramfs has already mounted the real root
**read-write** at `/`, and has mounted `/proc`, `/sys`, and `/dev`
and moved them into the real root. peinit therefore neither
assembles nor remounts the root, and does not blindly re-mount
those three pseudo-filesystems (see Phase 1, Steps 1-2). registryd's
storage backend requires a writable root (WAL and shared-memory
files) even for read-only registry operations; delivering the root
writable is the initramfs's responsibility, not peinit's.

peinit MUST NOT perform root filesystem assembly, decryption, or
repair. These operations require tools and configuration that
belong to the initramfs environment.

peinit starts with a minimal environment -- the initramfs provides
`TERM` only, with no `PATH` or other variables -- and an argv of
just its own path. peinit MUST NOT rely on inheriting any
environment from the initramfs, and MUST NOT pass its own
near-empty startup environment through to services; the base
environment handed to services is defined by peinit (see §4.1).

> [!INFORMATIVE]
> The initramfs is assembled by the Peios initramfs builder (mkirf)
> from hook scripts contributed by packages; mkirf resolves the hook
> ordering and bakes the sequence the initramfs PID 1 runs. Root
> storage assembly -- decryption, RAID/LVM activation, the root
> mount itself -- is performed by these hooks, not by peinit, and
> not by reading the registry at boot time. What peinit depends on
> is the handoff contract above, not the initramfs's internal
> configuration mechanism.

Non-root storage (data partitions, additional filesystems) is out
of scope for peinit. It is handled at the services/roles layer
(e.g. a Oneshot service that performs the mount), not by peinit
directly -- peinit has no built-in mount feature.

## Bootstrap identity model

The steady-state identity flow is: peinit requests a token from
authd, authd mints the token, peinit installs it on the service
process. But authd depends on lpsd, lpsd depends on registryd, and
registryd must start before any of them. The bootstrap model
resolves this.

**Platform services run as SYSTEM.** When peinit starts a service
during Phase 1 or a platform service during early Phase 2, it
MUST materialise a SYSTEM token (`S-1-5-18`) by minting one from
its own token (`kacs_create_token`; see §3.3) and install it on the
child process. No authd interaction is needed -- indeed authd does
not yet exist when these services start.

The following services use `Identity=SYSTEM`:

- **registryd** -- MUST start before authd exists
- **authd** -- needs SeTcbPrivilege and SeCreateTokenPrivilege; is
  the token minter for non-platform services
- **lpsd** -- MUST start before authd can resolve local identities
- **eventd** -- starts early, before authd is necessarily available

There is no allowlist restricting which services MAY use
`Identity=SYSTEM`. The security boundary is the registry key SD on
`Machine\System\Services\` -- an administrator who can create
service definitions is trusted to assign any identity.

peinit MUST include a per-service SID in the group list of every
SYSTEM token it mints. The SID is derived from the service name
using the service SID algorithm defined in PSD-004 (SID authority `S-1-5-80`, sub-authorities from
SHA-1 of the UTF-16LE uppercased service name). peinit computes
this independently -- no authd involvement is needed. This ensures
that platform services are distinguishable to AccessCheck despite
all running as SYSTEM.

> [!INFORMATIVE]
> This is the same model as Windows: SCM, LSASS, and core platform
> services all run as LocalSystem. The trust anchor is that peinit
> IS SYSTEM, and the kernel guarantees this via the boot token.

Once authd and lpsd are running, all subsequent services receive
tokens via the normal authd flow. Services with no Identity field
default to `LocalService` -- a well-known principal with minimal
privileges. For authd-minted tokens, authd automatically adds a
per-service SID to the token's group list.

## Phase 1

Phase 1 is compiled into peinit. It MUST NOT change at runtime and
has no registry dependency. Phase 1 performs the minimum operations
necessary to prepare the system for Phase 2.

### Step 1: Verify the root filesystem is writable

The initramfs delivers the real root mounted read-write (see the
initramfs contract). peinit MUST NOT remount the root -- root
assembly and mount flags are the initramfs's responsibility, and a
redundant remount of an already-writable or overlay root can fail
spuriously.

peinit MUST confirm the root is writable with a single probe write
(create, write, and remove one uniquely named file under `/.peinit/`).
If `/.peinit/` is absent, peinit MAY create it as part of the probe.
registryd's storage backend requires write access (WAL and
shared-memory files) even for read operations, so a read-only root
cannot support Phase 2.

If the probe write fails -- the root is unexpectedly read-only or
the filesystem is faulty -- peinit MUST enter Recovery mode.

### Step 2: Mount remaining virtual filesystems

The initramfs has already mounted `/proc`, `/sys`, and `/dev` and
moved them into the real root (see the initramfs contract). peinit
MUST NOT blindly re-mount them: a redundant mount stacks a second
filesystem over the populated one, and on some kernel/flag
combinations returns `EBUSY`.

peinit MUST ensure the following filesystems are present, mounting
each only if it is not already mounted:

| Mount point | Filesystem | Flags | Provided by |
|---|---|---|---|
| `/proc` | proc | nosuid, nodev, noexec | initramfs (mount only if absent) |
| `/sys` | sysfs | nosuid, nodev, noexec | initramfs (mount only if absent) |
| `/dev` | devtmpfs | nosuid | initramfs (mount only if absent) |
| `/dev/pts` | devpts | nosuid, noexec | peinit |
| `/dev/shm` | tmpfs | nosuid, nodev | peinit |
| `/run` | tmpfs | nosuid, nodev | peinit |
| `/sys/fs/cgroup` | cgroup2 | nosuid, nodev, noexec | peinit |

When invoking `mount(2)` for this table, peinit MUST pass the listed
`Filesystem` value as both the `source` and `filesystemtype` argument,
MUST pass only the listed flags, and MUST pass null mount data.

The mount set and flags are hardcoded; all seven MUST exist before
any other process runs. For the initramfs-provided mounts (`/proc`,
`/sys`, `/dev`), peinit MUST treat an already-mounted filesystem
(including an `EBUSY` result from an attempted mount) as success.

If a filesystem peinit is responsible for mounting (`/dev/pts`,
`/dev/shm`, `/run`, `/sys/fs/cgroup`) cannot be mounted, peinit MUST
enter Recovery mode.

### Step 3: Restore persisted random seed

peinit MUST attempt to restore the persisted random seed from
`/var/lib/peinit/random-seed` after `/dev` is available and before
registryd starts. The seed is a machine-local entropy cache for the
kernel CSPRNG. It is not configuration, and it MUST NOT be shipped in
packaged images, live ISOs, VM templates, or other cloned system
artifacts.

If the seed file is absent, peinit MUST treat this as a normal first-boot
or stateless-live-boot condition and continue. It MUST NOT enter Recovery
mode merely because no persisted seed exists. Environments that need strong
first-boot entropy for a stateless image MUST provide a kernel entropy
source such as hardware RNG or virtio-rng; a public seed in the image is
not an acceptable substitute.

If a seed file is present, peinit MUST mix it into the kernel random pool.
On Linux, peinit SHOULD use the random-device interface that credits entropy
for the locally persisted seed. If that interface is unavailable or fails,
peinit MAY still mix the bytes without crediting entropy, but MUST retain or
log the failure evidence and continue boot. A seed-restore failure MUST NOT
enter Recovery mode.

The initramfs MAY perform the same restore earlier once the persistent root
is mounted. peinit's Phase 1 restore remains required as a fallback for
non-participating initramfs images and non-initramfs boots.

### Step 4: Ensure local machine ID

peinit MUST ensure `/etc/machine-id` contains a stable local machine ID before
registryd or any Phase 2 service starts. This ID is a local opaque install ID
used for software compatibility, log correlation, D-Bus-style instance
identity, and similar infrastructure. It is distinct from Peios domain
machine identity and MUST NOT be treated as a security principal, credential,
SID, account, or authorization input.

The machine ID format is 128 bits encoded as exactly 32 lowercase hexadecimal
characters followed by a single newline. A valid existing file MUST be left
unchanged. If the file is absent, empty, or contains invalid contents, peinit
MUST generate a new 128-bit value from the kernel CSPRNG and atomically write a
valid file before continuing. Invalid non-empty contents MUST be retained or
logged as warning evidence, but MUST NOT enter Recovery mode.

Packaged images, live ISOs, VM templates, and other cloned system artifacts
MUST NOT ship a populated real machine ID. They MAY omit `/etc/machine-id` or
ship it empty as a reset marker. Clone/reset tooling that wants a new local
identity MUST remove or truncate `/etc/machine-id`; peinit will generate a new
ID on the next boot. Stateless live boots without persistent overlay get an
ephemeral ID for that boot.

The file is not secret and is expected to be readable by normal userspace, but
replacement is a system bootstrap operation and MUST be protected by Peios file
security so only SYSTEM-equivalent authority can create or replace it.

### Step 5: Set system clock from hardware RTC

peinit MUST read the hardware RTC and call `clock_settime()` to
initialise the system clock before registryd starts. This ensures
timestamps on registry operations, log entries, and the boot
attempt counter are meaningful.

On Linux, peinit MUST read the RTC via `RTC_RD_TIME` on `/dev/rtc`.
If `/dev/rtc` is absent, peinit MUST try `/dev/rtc0`. The returned
`struct rtc_time` value is interpreted as UTC and converted to
`CLOCK_REALTIME` seconds plus zero nanoseconds. If no RTC device can
be opened, the RTC read fails, the RTC value is invalid or
pre-Unix-epoch, `clock_settime(CLOCK_REALTIME, ...)` fails, or the
RTC file descriptor cannot be closed after a successful read, peinit
MUST enter Recovery mode.

> [!INFORMATIVE]
> NTP provides accurate time later in the boot process. This step
> gets the clock in the right ballpark so that early timestamps are
> not wildly wrong.

### Step 6: Start registryd

peinit has a compiled-in service definition for registryd:

| Field | Value |
|---|---|
| ImagePath | `/usr/sbin/registryd` |
| Identity | `SYSTEM` |
| Readiness | Notify (`READY=1` via sd_notify) |
| ErrorControl | Critical |

peinit MUST:

1. Mint a SYSTEM token from its own token (`kacs_create_token`),
   including registryd's per-service SID in the group list (derived
   per the PSD-004 service SID algorithm).
2. Create registryd's cgroup tree under
   `/sys/fs/cgroup/peinit/`.
3. Fork, install the token on the child, and exec
   `/usr/sbin/registryd`.
4. Wait for `READY=1` via sd_notify with a hardcoded timeout
   (implementation-defined).

registryd's `READY=1` MUST mean "accepting and serving registry
requests" -- not merely "process is alive." registryd MUST NOT
send `READY=1` until its storage backend is open, its schema is
validated, and it can handle reads.

After receiving `READY=1`, peinit MUST perform a probe read of
`Machine\System\Services\SchemaVersion` (the schema-version guard;
see §3.2 and the appendix) to verify the registry is serving reads.
This key is guaranteed to exist on any valid system. If the probe
read fails or times out, peinit MUST treat registryd as failed.
The probe is successful only if the value is present and decodes as
the schema-version `REG_DWORD`; a missing value, type mismatch, or
malformed payload is a probe failure.

When registryd passes readiness and the schema-version probe, peinit
MUST retain the activation as a normal runtime service instance. The
retained record MUST include the service state, pidfd-tracked main
process identity, cgroup generation and paths, output-pipe ownership,
notify generation, job identity, and any cleanup evidence needed to
supervise, stop, restart, or report the service later. Peinit MUST NOT
discard this ownership at the Phase 2 boundary.

During Phase 2 service-model materialisation, the registry definition
for `registryd` is merged onto the retained Phase 1 activation. Peinit
MUST NOT create a second inactive `registryd` runtime record and MUST
NOT restart registryd merely because the registry definition has been
loaded. If the registry definition for `registryd` is absent or invalid,
the normal complete-graph validation rules apply before Phase 2 boot
continues.

If registryd fails to start, its readiness timeout expires, or the
probe read fails, peinit MUST enter Recovery mode. There is no
Phase 2 without a working registry.

### Step 7: Provision boot-time paths

After registryd is running and before Phase 2 services are planned
or started, peinit MUST read and apply boot-time path provisioning
entries from `Machine\System\Init\ProvisionedPaths\`. This is the
registry-backed equivalent of the tmpfiles.d role: it creates
boot-scoped or persistent filesystem objects that are not owned by
one service definition, and applies Peios file security descriptors
to them.

Each child key under `Machine\System\Init\ProvisionedPaths\` is one
provisioning entry. Unknown values on an entry are ignored. Unknown
or malformed entries are logged as warnings and skipped; they MUST
NOT by themselves enter Recovery mode.

| Value | Type | Required | Default | Description |
|---|---|---|---|---|
| `Kind` | string | yes | -- | `directory` or `file`. |
| `Path` | string | yes | -- | Absolute path to create or verify. |
| `Security` | binary | no | built-in default | Peios file security descriptor to apply to the target object. |
| `Required` | dword | no | 0 | If 1, failure to provision this entry prevents Phase 2 and enters Recovery mode. |

For `Kind=directory`, peinit MUST ensure `Path` exists as a
directory and MUST fail the entry if the path exists with another
file type. For `Kind=file`, peinit MUST ensure `Path` exists as a
regular file and MUST fail the entry if the path exists with another
file type. `Kind=file` MUST NOT truncate an existing file. peinit
MUST NOT create unspecified parent directories for a provisioning
entry; packages that need a hierarchy MUST define each required
directory explicitly or depend on the package that owns the parent.

When `Security` is absent, peinit applies a built-in default SD that
grants SYSTEM and Administrators full access and grants ordinary
users read/traverse access. When `Security` is present, peinit
applies the supplied binary Peios security descriptor. A malformed
or rejected descriptor fails that entry.

Entries with `Required=0` are fail-soft: peinit logs the failure and
continues. Entries with `Required=1` are fail-closed: peinit logs
the failure and enters Recovery mode before Phase 2 starts. This
allows packages to mark paths that are essential to boot separately
from best-effort compatibility paths.

### Step 8: Infrastructure setup

After registryd is running, peinit MUST perform the following
infrastructure setup before Phase 2 begins:

1. **Control socket creation.** peinit MUST create its control
   socket at `/run/peinit/control.sock`. The socket is used for
   all runtime commands for the lifetime of the system.
2. **JFS device opening.** peinit MUST open `/dev/jfs` and add the
   fd to its event loop. This enables ad-hoc job submission from
   services once Phase 2 starts.
3. **Loopback interface bring-up.** peinit MUST bring up the
   loopback interface (`lo`) via a netlink call. Services that bind
   to `127.0.0.1` (authd, eventd, etc.) require the loopback
   interface to be operational.

If control socket creation fails, peinit MUST enter Recovery mode.
JFS device open failure, JFS event-loop registration failure, and
loopback bring-up failure MUST be logged as warnings but MUST NOT
prevent Phase 2 from starting.

## Phase 1 failure summary

Most Phase 1 failures are fatal to boot. Recovery mode is the only
option for failures that prevent Phase 2 from starting with working
infrastructure. Explicitly fail-open bootstrap best-effort operations
are called out below.

| Failure | Response |
|---|---|
| Root writability probe fails | Recovery mode |
| A peinit-owned virtual filesystem (`/dev/pts`, `/dev/shm`, `/run`, `/sys/fs/cgroup`) fails to mount | Recovery mode |
| `/proc`, `/sys`, or `/dev` already mounted (`EBUSY`) | Tolerated -- treated as success |
| Persisted random seed is absent or cannot be restored | Warning/no-op; Phase 2 continues |
| `/etc/machine-id` is absent, empty, or invalid | Generate/replace and continue |
| registryd fails to start | Recovery mode |
| registryd sends READY=1 but probe read fails | Recovery mode |
| registryd readiness timeout expires | Recovery mode |
| Provisioned path entry is malformed | Warning logged, entry skipped |
| Optional provisioned path cannot be created or secured | Warning logged, Phase 2 continues |
| Required provisioned path cannot be created or secured | Recovery mode |
| Control socket creation fails | Recovery mode |
| JFS device open fails | Warning logged, Phase 2 continues |
| JFS event-loop registration fails | Warning logged, Phase 2 continues |
| Loopback bring-up fails | Warning logged, Phase 2 continues |
