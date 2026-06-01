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
(create and remove a file under `/.peinit/`). registryd's storage
backend requires write access (WAL and shared-memory files) even
for read operations, so a read-only root cannot support Phase 2.

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

The mount set and flags are hardcoded; all seven MUST exist before
any other process runs. For the initramfs-provided mounts (`/proc`,
`/sys`, `/dev`), peinit MUST treat an already-mounted filesystem
(including an `EBUSY` result from an attempted mount) as success.

If a filesystem peinit is responsible for mounting (`/dev/pts`,
`/dev/shm`, `/run`, `/sys/fs/cgroup`) cannot be mounted, peinit MUST
enter Recovery mode.

### Step 3: Set system clock from hardware RTC

peinit MUST read the hardware RTC and call `clock_settime()` to
initialise the system clock before registryd starts. This ensures
timestamps on registry operations, log entries, and the boot
attempt counter are meaningful.

> [!INFORMATIVE]
> NTP provides accurate time later in the boot process. This step
> gets the clock in the right ballpark so that early timestamps are
> not wildly wrong.

### Step 4: Start registryd

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

If registryd fails to start, its readiness timeout expires, or the
probe read fails, peinit MUST enter Recovery mode. There is no
Phase 2 without a working registry.

### Step 5: Infrastructure setup

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
JFS device open failure and loopback bring-up failure MUST be
logged as warnings but MUST NOT prevent Phase 2 from starting.

## Phase 1 failure summary

All Phase 1 failures are fatal to boot. Recovery mode is the only
option because Phase 2 cannot begin without working infrastructure.

| Failure | Response |
|---|---|
| Root writability probe fails | Recovery mode |
| A peinit-owned virtual filesystem (`/dev/pts`, `/dev/shm`, `/run`, `/sys/fs/cgroup`) fails to mount | Recovery mode |
| `/proc`, `/sys`, or `/dev` already mounted (`EBUSY`) | Tolerated -- treated as success |
| registryd fails to start | Recovery mode |
| registryd sends READY=1 but probe read fails | Recovery mode |
| registryd readiness timeout expires | Recovery mode |
| Control socket creation fails | Recovery mode |
| JFS device open fails | Warning logged, Phase 2 continues |
| Loopback bring-up fails | Warning logged, Phase 2 continues |
