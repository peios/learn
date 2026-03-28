---
title: What Is Provium
type: concept
order: 10
description: Provium is a KVM test harness that lets you write tests in Lua and run them against real virtual machines. No mocks, no simulations — real kernels, real syscalls.
---

Provium is a test harness for Linux kernel modules and system-level code. You write tests in Lua, and Provium runs them against real QEMU/KVM virtual machines. Every syscall, every ioctl, every file operation happens inside an actual kernel — not a mock or simulation.

## Why Provium exists

Testing kernel modules is hard. The traditional approach involves writing tests in C, compiling them against kernel headers, copying them into a VM, running them manually, and parsing the output. The feedback loop is slow and the boilerplate is heavy.

Provium replaces this workflow. A test is a `.lua` file that creates a VM, boots a kernel, and drives it through a high-level API. The same operations that would require hundreds of lines of C — building structs, packing binary data, issuing syscalls, checking results — take a handful of Lua calls.

## Key features

| Feature | Description |
|---|---|
| **Real VMs** | Tests run against actual QEMU/KVM virtual machines with real Linux kernels. No mocking, no simulation. |
| **Lua scripting** | Write tests in Lua instead of C. No recompilation, fast iteration. |
| **No networking required** | Host-guest communication uses vsock (virtio sockets). No IP stack, no network configuration. |
| **Raw syscall access** | Call any syscall from Lua with `vm:syscall()`. Build binary structs with `provium.pack()`. |
| **Fixtures** | Cache booted VM state as snapshots. Tests resume from a snapshot instead of cold-booting — a fixture resume takes a fraction of a cold boot. |
| **Parallel execution** | Run tests concurrently with automatic resource pooling. Provium gates VM launches against available memory and CPU. |
| **Workers** | Fork the guest agent to test multi-process scenarios. Each worker has independent credentials and its own command channel. |
| **Sub-tests** | Organize multiple assertions into named `test()` blocks within a single file. Failures are isolated and reported individually. |

## How it works

Provium has two components: a **host binary** (written in Go) and a **guest agent** (written in C).

```
Lua test script (host)
    ↓
provium binary (Go)
    ↓ vsock
guest agent (C, inside QEMU/KVM)
    ↓
kernel (syscalls, ioctls, file ops)
```

The host binary embeds a Lua runtime and the guest agent. When a test creates a VM, Provium:

1. Launches QEMU with the configured kernel and initramfs
2. Injects the guest agent into the VM via a shim initramfs
3. Connects to the agent over vsock
4. Exposes the agent's capabilities through the Lua API

From there, the test script drives the VM: executing shell commands, reading and writing files, issuing raw syscalls and ioctls, and asserting on the results.

## What it is not

Provium is **general-purpose** — it is not specific to any particular kernel module. Any kernel that boots in QEMU can be tested with Provium. It is also not a unit testing framework for userspace code. If your code runs in userspace and doesn't need a real kernel, use a standard test framework instead.

## How it compares

| | Provium | kselftest | ktest | LTP |
|---|---|---|---|---|
| **Language** | Lua | C/shell | Shell/config | C/shell |
| **VM management** | Built-in | External | External | External |
| **Binary struct building** | `provium.pack()` | Manual C structs | N/A | Manual C structs |
| **Snapshot caching** | Built-in fixtures | No | No | No |
| **Parallel execution** | Built-in | Partial | No | Partial |
| **Multi-process testing** | `vm:spawn()` workers | fork() in C | No | fork() in C |
