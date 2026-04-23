---
title: Snapshots and Fixtures
type: concept
description: How Provium saves and restores VM state using QEMU's migration mechanism to make fixture-based testing fast.
related:
  - provium/writing-tests/fixtures
  - provium/architecture/how-provium-works
---

Fixtures depend on QEMU's snapshot mechanism — the ability to save a VM's complete state to a file and restore it later. This page explains how that works under the hood.

## QEMU Machine Protocol (QMP)

Provium communicates with QEMU through **QMP** — a JSON-based control protocol over a Unix socket. QMP provides commands for pausing, resuming, migrating, and inspecting the VM.

When a VM is booted with snapshot support enabled (which happens automatically for fixture builds), Provium:

1. Passes `-qmp unix:/path/to/socket,server,wait=off` to QEMU
2. Connects to the QMP socket after QEMU starts
3. Uses QMP commands to save and restore state

## Saving state

When a fixture script completes, Provium saves the VM's state:

1. **Disconnect the agent.** The host closes its vsock connection. The agent detects EOF and returns to its `accept()` loop — this is critical because the snapshot must capture the agent ready to accept a new connection, not blocked on a read from a stale one.
2. **Wait briefly.** A short delay (200ms) ensures the agent has returned to the accept loop.
3. **Pause the VM.** QMP `stop` command freezes execution.
4. **Migrate to file.** QMP `migrate file:/path/to/snapshot` saves the full VM state — memory, device state, CPU registers — to a file.
5. **Wait for completion.** Provium polls QMP until the migration status is `completed`.

The snapshot file contains everything needed to resume the VM exactly where it left off.

## Restoring state

When a test calls `provium.fixture("name")`:

1. **Start QEMU with incoming migration.** The VM is launched with `-incoming file:/path/to/snapshot`, which tells QEMU to load state instead of booting.
2. **Connect QMP.** Provium connects to the QMP socket.
3. **Sync vsock CID.** Migration may restore the vsock CID from the snapshot, overriding the command-line value. Provium attempts to set the desired CID via `qom-set`. If that fails (the property may be read-only), it reads the actual CID via `qom-get` and updates its connection address.
4. **Resume execution.** QMP `cont` command unpauses the VM.
5. **Connect to agent.** The agent is already listening (it was in the accept loop when the snapshot was taken). The host connects to vsock and receives `MSG_READY`.

The VM is now in exactly the state it was in when the fixture script completed — all mounted filesystems, loaded kernel modules, written files, and configured state are present.

## CID allocation

Each VM gets a unique Context ID (CID) for vsock communication. CIDs are allocated sequentially starting at 10 (CIDs 0-2 are reserved by the vsock protocol).

When restoring from a snapshot, the vsock device may retain the original CID from the snapshot rather than the new CID assigned on the command line. Provium handles this by querying and, if necessary, updating its CID tracking after resume.

## Fixture caching

The fixture manager caches snapshots for the duration of a test run:

- Snapshots are stored in `/tmp/provium-runs/run-*/fixtures/`
- Each fixture gets one snapshot file (e.g., `kacs.snapshot`)
- Building is lazy — the first request triggers the build
- Building is thread-safe — concurrent requests for the same fixture block until the first build completes (using `sync.Once`)
- Snapshots are deleted when the test run finishes

Snapshots are not persisted between runs. Each `provium test` invocation rebuilds fixtures from scratch. This ensures fixtures always reflect the current state of the kernel and test code.
