---
title: Bootstrap
---

peinit's boot has two phases: a hardcoded bootstrap that brings up
the minimum infrastructure, and a registry-driven phase that starts
everything else. The boundary between them is registryd. This
section defines Phase 1 and the identity model that governs early
boot.

## Initramfs contract

peinit assumes the root filesystem is fully assembled, checked,
and mountable when it starts. Root storage assembly -- LUKS
decryption, LVM activation, RAID array assembly, filesystem checks
-- is handled entirely by the initramfs before peinit runs.

The initramfs performs `switch_root` and transfers control to
peinit as PID 1. peinit MUST NOT perform root filesystem assembly,
decryption, or repair. These operations require tools and
configuration that belong to the initramfs environment.

> [!INFORMATIVE]
> Root storage configuration lives in the registry under
> `Machine\System\Boot\RootStorage\`. When an administrator changes
> root storage settings, the initramfs image is regenerated to bake
> in the updated configuration. The initramfs itself contains no
> registry infrastructure -- it uses flat, baked-in configuration
> extracted from the registry at build time.

Non-root storage (data partitions, additional filesystems) is
handled by mount pseudo-services in Phase 2.

## Bootstrap identity model

The steady-state identity flow is: peinit requests a token from
authd, authd mints the token, peinit installs it on the service
process. But authd depends on lpsd, lpsd depends on registryd, and
registryd must start before any of them. The bootstrap model
resolves this.

**Platform services run as SYSTEM.** When peinit starts a service
during Phase 1 or a platform service during early Phase 2, it
MUST clone its own SYSTEM token (`S-1-5-18`) via
`kacs_duplicate_token` and install the clone on the child process.
No authd interaction is needed.

The following services use `Identity=SYSTEM`:

- **registryd** -- MUST start before authd exists
- **authd** -- needs PRIV_TCB and PRIV_CREATE_TOKEN; is the token
  minter
- **lpsd** -- MUST start before authd can resolve local identities
- **eventd** -- starts early, before authd is necessarily available

There is no allowlist restricting which services MAY use
`Identity=SYSTEM`. The security boundary is the registry key SD on
`Machine\System\Services\` -- an administrator who can create
service definitions is trusted to assign any identity.

peinit MUST add a per-service SID to the group list of every
cloned SYSTEM token. The SID is derived from the service name
using the service SID algorithm defined in the KACS v0.20
specification (SID authority `S-1-5-80`, sub-authorities from
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

### Step 1: Remount root filesystem read-write

The Linux kernel typically mounts the root filesystem read-only.
peinit MUST remount it read-write before any other operation.
registryd's storage backend requires write access (WAL and shared-
memory files) even for read operations.

If the remount fails, peinit MUST enter Recovery mode.

### Step 2: Mount virtual filesystems

peinit MUST mount the following virtual filesystems:

| Mount point | Filesystem | Flags |
|---|---|---|
| `/proc` | proc | nosuid, nodev, noexec |
| `/sys` | sysfs | nosuid, nodev, noexec |
| `/dev` | devtmpfs | nosuid |
| `/dev/pts` | devpts | nosuid, noexec |
| `/dev/shm` | tmpfs | nosuid, nodev |
| `/run` | tmpfs | nosuid, nodev |
| `/sys/fs/cgroup` | cgroup2 | nosuid, nodev, noexec |

The mount set and flags are hardcoded. These filesystems MUST
exist before any other process runs.

If any mount fails, peinit MUST enter Recovery mode.

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

1. Clone its own SYSTEM token and add the per-service SID for
   registryd (derived per the KACS v0.20 service SID algorithm).
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

After receiving `READY=1`, peinit MUST perform a probe read: a
read of a known registry key to verify the registry is functional.
If the probe fails or times out, peinit MUST treat registryd as
failed.

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
| Root remount fails | Recovery mode |
| Virtual filesystem mount fails | Recovery mode |
| registryd fails to start | Recovery mode |
| registryd sends READY=1 but probe read fails | Recovery mode |
| registryd readiness timeout expires | Recovery mode |
| Control socket creation fails | Recovery mode |
| JFS device open fails | Warning logged, Phase 2 continues |
| Loopback bring-up fails | Warning logged, Phase 2 continues |
