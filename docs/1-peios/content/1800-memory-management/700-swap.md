---
title: Swap
type: concept
description: Swap on Peios — what it is, the SeCreatePagefilePrivilege model for swapon/swapoff, swap files vs partitions, and the boot-time activation pattern.
related:
  - peios/memory-management/overcommit-and-oom
  - peios/memory-management/page-cache
  - peios/privileges/se-create-pagefile-privilege
---

**Swap** is disk space the kernel can use as an overflow for physical memory. When RAM pressure rises, the kernel selects cold pages — pages that haven't been accessed recently — and writes their contents to swap, freeing the physical page for active use. When the swapped-out page is later accessed, a page fault triggers the kernel to read it back, evicting some other cold page in the process.

Swap turns a hard memory ceiling into a softer one. A system with 16 GB of RAM and 32 GB of swap can keep 48 GB of working set "alive" — at the cost of dramatic latency on accesses that hit swap. Swap is not a substitute for RAM; it's a buffer that delays OOM.

This page covers swap setup and admin model on Peios, the privilege gate, and the relationship with peinit at boot.

## Why swap is privileged

Swap is one of the few operations on a Peios system that affects every running process at once and provides a path to read other processes' memory. The privilege model reflects that.

When the kernel pages out a cold page, the contents are written verbatim to the swap device. Whoever controls the device — anyone with read access to the underlying disk — can read every page that has ever been swapped out. This includes:

- Cryptographic keys (unless the holder used `mlock` or `memfd_secret`).
- Authentication tokens that lived in process memory.
- Decrypted file contents from anywhere in the page cache.
- Any other secret a process happened to have in memory at the moment the kernel decided to evict it.

The standard privilege model gates **adding swap** so that an attacker cannot present their own block device as a swap target and let the kernel feed memory contents into it. It also gates **removing swap** because `swapoff` on an active swap device can crash the kernel if RAM cannot accommodate the swapped-in contents.

## SeCreatePagefilePrivilege

`swapon(path, flags)` and `swapoff(path)` require **`SeCreatePagefilePrivilege`**. This is a dedicated privilege — not bundled with `SeTcbPrivilege` — so that a swap-management daemon or admin tool can be granted exactly the authority it needs without inheriting the rest of TCB-tier capability.

Default holders:

- **peinit** at boot, applying the configured swap layout from registry-driven config.
- **Admin tools** (e.g. a hypothetical `pe-swap` utility) when invoked by an administrator who holds the privilege.

The privilege is **not** held by the interactive admin shell by default — picking it up requires explicit elevation. This matches the general Peios pattern: privileges are operational tools, granted to the specific tool that needs them, not blanket-granted to whoever happens to be logged in as administrator.

`mkswap` (the userspace tool that writes the swap header to a file or partition) is **unprivileged** — it just writes a specific 4 KB header to a file. The thing that requires the privilege is `swapon`, which makes the kernel start using that file as backing store. This split is intentional: the installer can prepare swap files at install time without needing runtime privileges; only the activation needs the gate.

## Swap topology

Peios recognises both forms of swap target:

| Target | Setup |
|---|---|
| **Swap partition** | A whole block device or partition formatted with `mkswap`, then activated with `swapon`. Faster than swap files (no filesystem layer), at the cost of pre-allocated capacity. |
| **Swap file** | A regular file on a filesystem, formatted with `mkswap`, then activated. Slightly slower (extra filesystem indirection), but resizable and easier to add post-install. |

Multiple swap targets can be active simultaneously, each with a configurable **priority** (higher numbers preferred). A common pattern is a high-priority small swap file on fast storage (NVMe) backed up by a lower-priority large swap partition on slower storage; the kernel prefers the fast target until it fills, then falls back.

Per-target configuration lives in the registry and is read by peinit at boot:

```
HKLM\System\CurrentControlSet\Services\Swap\<name>
  Path = "/var/lib/swap/swap0"   (or "/dev/sda3" for partitions)
  Priority = 10
  Active = 1
```

peinit, holding `SeCreatePagefilePrivilege` by birthright, walks the configured entries and calls `swapon` for each `Active = 1` entry.

## swappiness

The `swappiness` tunable controls how aggressively the kernel prefers swapping over reclaiming page cache. Range `0`–`200`:

| Value | Behaviour |
|---|---|
| `0` | Swap only when absolutely necessary. The kernel will reclaim file-backed pages from the page cache first. |
| `60` (default) | Balanced — swap and page cache reclaim roughly proportional to their sizes. |
| `100` | Equal preference between swap and page cache. |
| `200` | Aggressive swapping — even pages with cache backing get swapped before file-backed pages get evicted. |

The right value depends on workload. Database servers often run at `0` or `1` (the cache is more valuable than swapping out anonymous memory). Desktop systems use `60`. Burst workloads with large transient working sets sometimes go higher.

`swappiness` is registry-driven via ksyncd. The setting can also be set per-cgroup (cgroup v2 memory controller) — see Resource Control.

## zswap and zram

Two related compression mechanisms reduce the cost of swapping:

| Mechanism | What it does |
|---|---|
| **zswap** | A compressed cache *in front of* swap. Pages headed for swap-out are first compressed and held in a kernel-managed RAM pool; only when the pool fills do pages actually go to disk. Reads come from the compressed pool when possible, avoiding the disk round-trip. |
| **zram** | A compressed RAM-backed *block device* you can use as swap. No physical disk is touched at all; "swap" is just compressed RAM. |

zswap is the right choice when you have moderate swap pressure and want to reduce disk I/O. zram is the right choice for memory-constrained systems with no disk for swap (small VMs, embedded systems) — it trades CPU cycles for effective memory expansion.

Both are kernel features; their setup is admin-tier configuration via the registry. zram device creation requires `SeTcbPrivilege` (it manipulates the block device subsystem); using a zram device as swap thereafter follows the normal `swapon` privilege model.

## MADV_PAGEOUT and proactive eviction

`madvise(addr, len, MADV_PAGEOUT)` tells the kernel "evict these pages now." For anonymous memory, this means writing them to swap if any swap is configured. The call is unprivileged — a process is free to ask the kernel to evict its own memory. This is useful for explicit cache-pressure tools and for memory-budgeted services that want to release inactive caches before the kernel decides to.

`MADV_COLD` is the lighter version: move pages to the inactive LRU list, making them more likely candidates for future eviction without forcing immediate eviction.

Cross-process variants — using `process_madvise(PIDFD, MADV_PAGEOUT)` on another process — follow the standard cross-process gate of `PROCESS_VM_WRITE` plus PIP dominance. This is the primitive that container supervisors and memory-pressure daemons use to proactively trim idle workers.

## RLIMIT_SWAP and cgroup integration

There is no per-process `RLIMIT_SWAP` — swap usage is bounded at the system level by total swap capacity, and at the cgroup level by `memory.swap.max`. The cgroup memory controller documents the per-group bounding mechanism in the **Resource Control** category.

A workload running in a cgroup with `memory.swap.max = 0` cannot swap at all — pages that would be swapped are instead reclaimed (if file-backed) or contribute to OOM pressure (if anonymous). This is sometimes desired for workloads that should never tolerate swap latency.

## Swap-over-NFS and remote swap

The kernel supports swapping to NFS-mounted files, but only with significant operational caveats: the remote filesystem must be available at all times, network latency directly affects swap latency, and connection failures cause severe stalls. Peios honours the capability for compatibility but the default-image policy is to refuse `swapon` on network-backed paths unless the calling process holds `SeTcbPrivilege` in addition to `SeCreatePagefilePrivilege`. This is a compatibility deference; the recommendation is to never swap over NFS.

Other remote-swap configurations (iSCSI, SMB) follow the same logic: privileged-only by default policy because the failure modes are too consequential for routine setup.

## Swap and OOM

Swap delays the OOM killer but does not prevent it. A workload that exhausts both RAM and swap reaches the same OOM-killer code path as a swapless system; swap just postpones the moment.

This means swap sizing should reflect the workload's tolerance for paging latency: enough swap to absorb transient bursts without paging-induced thrash, but not so much that the system can spend hours in a degraded state instead of triggering OOM and recovering. There is no universal correct sizing.

## See also

- [Overcommit and OOM](overcommit-and-oom) — what happens when swap fills up.
- [Page Cache](page-cache) — the file-backed pages that compete with swap for reclaim.
- [Memory Locking](memory-locking) — `mlock` and `memfd_secret` as the way to keep secrets out of swap.
