---
title: Guest Agent
type: concept
description: The guest agent is a statically-linked C binary that runs inside the VM, executing commands and syscalls on behalf of the host.
related:
  - provium/architecture/how-provium-works
  - provium/architecture/wire-protocol
---

The guest agent is the component that runs inside the VM. It receives messages from the host over vsock, executes the requested operations against the real kernel, and sends results back. The agent is what makes Provium's Lua API work — every `vm:exec()`, `vm:syscall()`, and `vm:read_file()` call translates into a message to the agent.

## How it gets into the VM

The agent is embedded in the Provium binary at build time. When a test boots a VM, Provium:

1. Extracts the agent binaries (`provium-agent` and `provium-wrapper`) to a temp directory
2. Builds a shim initramfs (cpio archive) containing these binaries
3. Concatenates the shim with the user's initramfs (the kernel supports multiple cpio archives)
4. Passes the combined initramfs to QEMU

The kernel boots, unpacks both cpio archives (the user's and the shim), and runs `provium-wrapper` as init.

## The wrapper

`provium-wrapper` is the entry point. It:

1. Starts `provium-agent` in the background
2. Execs the real init binary (specified by the `provium.init=` kernel parameter)

This ensures the agent is running before the real init starts, and the init binary becomes PID 1 as expected.

## Agent startup

The agent:

1. Opens a vsock listener on port 5123
2. Waits for a connection from the host
3. Sends `MSG_READY` to signal that it is initialized
4. Enters a message loop, processing requests until the connection closes or a shutdown is requested

## Statically linked

The agent is compiled with musl (static linking). It has no runtime dependencies — no libc, no dynamic linker, no shared libraries. This means it works in any initramfs, regardless of what userspace libraries are available. It runs in a minimal busybox environment just as well as a full distribution.

## Worker processes

When the host sends `MSG_SPAWN_WORKER`, the agent forks (or clones with CLONE_THREAD). The child process:

1. Closes the parent's vsock connection
2. Opens a new vsock listener on a fresh port
3. Sends `MSG_WORKER_STARTED` (via the parent) with the new port number
4. Enters its own message loop

The host connects to the worker's port and communicates with it independently. Each worker is a separate process (or thread, in clone mode) with its own credentials and command channel.

### Fork vs clone

- **Fork** (default): The worker gets a new PID, address space (copy-on-write), file descriptor table, and credentials. Changes in the worker do not affect the parent.
- **Clone with CLONE_THREAD**: The worker shares the parent's address space and file descriptor table but has independent credentials. This is useful for testing per-thread credential behavior while sharing open file descriptors.

## Shutdown

When the host sends `MSG_SHUTDOWN`:

1. The agent sends a `MSG_READY` acknowledgment
2. The agent writes `o` to `/proc/sysrq-trigger` to trigger an immediate power-off
3. QEMU exits

The acknowledgment is sent before the power-off so the host knows the command was received. The host then waits for the QEMU process to exit.
