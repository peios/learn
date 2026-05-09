---
title: How Provium Works
type: concept
description: Provium's architecture — a Go host binary with an embedded Lua runtime drives a C agent inside a QEMU/KVM virtual machine over vsock.
related:
  - provium/architecture/wire-protocol
  - provium/architecture/guest-agent
  - provium/architecture/snapshots
---

Provium has two components: a **host binary** written in Go and a **guest agent** written in C. They communicate over **vsock** — a direct host-guest socket mechanism that requires no IP networking.

## Architecture overview

```
┌──────────────────────────────────┐
│  Host                            │
│                                  │
│  provium binary (Go)             │
│    ├─ Lua runtime (gopher-lua)   │
│    ├─ Test runner (parallel)     │
│    ├─ Fixture manager (snapshots)│
│    ├─ Resource pool              │
│    └─ Protocol client            │
│         │                        │
│         │ vsock                   │
│         ▼                        │
│  ┌────────────────────────────┐  │
│  │  QEMU/KVM                  │  │
│  │                            │  │
│  │  Linux kernel              │  │
│  │    ↕ syscalls              │  │
│  │  provium-agent (C)         │  │
│  │    ├─ Command executor     │  │
│  │    ├─ File I/O             │  │
│  │    ├─ Syscall proxy        │  │
│  │    ├─ Job manager          │  │
│  │    └─ Worker spawner       │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

## Host side

The host binary is a single Go executable that embeds:

- **Lua runtime** ([gopher-lua](https://github.com/yuin/gopher-lua)) — executes test scripts
- **Provium API** — Lua bindings for VM management, syscalls, file I/O, and assertions
- **Test runner** — discovers test files, runs them in parallel, reports results
- **Fixture manager** — builds and caches VM snapshots lazily, thread-safe
- **Resource pool** — gates VM launches against available memory and CPU
- **Protocol client** — sends messages to the guest agent over vsock
- **Embedded agent** — the guest agent binaries are compiled into the Go binary

When you run `provium test tests/`, the host binary:

1. Extracts the embedded agent binaries to a temp directory
2. Loads `provium.toml` for profile definitions
3. Discovers `.lua` test files
4. Runs each test in a Lua VM, creating QEMU processes as needed

## Guest side

The guest agent (`provium-agent`) is a statically-linked C binary built with musl. It is injected into the VM via a shim initramfs that overlays the user's initramfs.

### Boot sequence

1. The kernel boots and runs `provium-wrapper` as init (or rdinit)
2. The wrapper starts the agent in the background
3. The agent listens on vsock port 5123
4. The wrapper execs the real init binary (`provium.init=` kernel parameter)
5. Once the agent receives a connection, it sends `MSG_READY`
6. The host proceeds to run the test

### Agent capabilities

The agent handles these operations:

| Operation | Description |
|---|---|
| **exec** | Run a shell command, return exit code + stdout + stderr |
| **write_file** | Write data to a guest file |
| **read_file** | Read a guest file |
| **syscall** | Execute a raw syscall with integer and buffer arguments |
| **ioctl** | Execute an ioctl on a guest fd |
| **background** | Start a command asynchronously |
| **job_wait/kill** | Manage background jobs |
| **spawn_worker** | Fork the agent process |
| **shutdown** | Power off the guest |

## Communication: vsock

Provium uses **virtio-vsock** (AF_VSOCK) for host-guest communication. Vsock provides socket semantics without requiring an IP stack:

- No network interfaces to configure
- No DHCP, DNS, or routing
- Direct, low-latency host-guest connection
- Each VM gets a unique Context ID (CID), starting at 10

The vsock device is attached to the VM automatically. The agent listens on port 5123. The host connects using the VM's CID.

## KVM acceleration

If `/dev/kvm` is available, Provium passes `-enable-kvm` to QEMU for hardware-accelerated virtualization. This is the expected mode for development and CI. Without KVM, QEMU falls back to software emulation — tests still work but run significantly slower.
