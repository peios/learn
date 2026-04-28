---
title: Linux Compatibility
type: concept
description: How cgroups appear to unmodified Linux applications — v2-only paths, the device controller's composition with KACS, the dropped v1 controllers, and the file-mode-vs-DACL transition.
related:
  - peios/resource-management/understanding-cgroups
  - peios/resource-management/working-with-cgroups
  - peios/linux-compatibility/credential-projection
---

Peios is built on a Linux kernel base. Linux applications that have not been ported to Peios-native APIs still drive cgroups through `/sys/fs/cgroup`. Peios honours the cgroupfs interface so unmodified container runtimes, init systems, and self-introspecting runtimes continue to work, while replacing the UNIX-permissions access surface with KACS DACLs and dropping legacy paths.

This page documents the legacy compatibility surface for cgroups. Native Peios applications use the standard filesystem API and DACLs documented elsewhere; this page covers what unmodified Linux software encounters.

## v2-only

cgroup v1 is not supported. Applications that mount per-controller hierarchies, write to `tasks` files, or rely on v1-only controllers will fail.

What this means concretely:

| v1 feature | Status on Peios |
|---|---|
| Per-controller mount points (`mount -t cgroup -o cpu cgroup_cpu /sys/fs/cgroup/cpu`) | Mount fails — only the unified hierarchy is mountable |
| `tasks` file (per-controller thread membership) | Not present — use `cgroup.threads` (v2 threaded mode) |
| `release_agent` notification | Not supported — use inotify on `cgroup.events` |
| `notify_on_release` | Not supported |
| `cpu.shares` (v1 weight) | Not present — use `cpu.weight` |
| `cpu.cfs_quota_us` / `cpu.cfs_period_us` | Not present — use `cpu.max` |
| `memory.limit_in_bytes` | Not present — use `memory.max` |
| `blkio.*` | Not present — use `io.*` |
| `freezer.state` (THAWED/FREEZING/FROZEN) | Not present — use `cgroup.freeze` |
| `devices.allow` / `devices.deny` (v1 device cgroup) | Not present — see device controller below |
| `net_cls`, `net_prio` controllers | Not present — Peios uses nftables and eBPF for packet classification |
| `perf_event` v1 controller | Not present — Peios uses v2 perf cgroup integration |

Software pinned to cgroup v1 must be updated to use v2 paths. Most modern container runtimes and init systems support both; configuration may need to specify v2.

The hybrid mode (`cgroup_no_v1=` boot parameter to disable individual v1 controllers while keeping v1 mounts available) is also not supported. Either v2 is in use, or the application will fail to mount cgroups.

## The `nsdelegate` mount option

The `nsdelegate` mount option exists on Linux to make cgroup namespace boundaries act as delegation boundaries — a process inside a cgroup namespace can only manage cgroups within its view. The pattern enables **rootless containers**: a user namespace + cgroup namespace + `nsdelegate` lets an unprivileged user manage their own cgroup hierarchy without reaching the host's.

Peios rejects user namespaces and does not support rootless containers, so the use case for `nsdelegate` does not exist on Peios. The mount option is accepted at mount time for compatibility (no error) but has no effect — the security boundaries `nsdelegate` would create are already provided by silos and KACS DACLs in any container pattern Peios supports.

## The unified hierarchy and `cgroup.subtree_control`

The single mount point at `/sys/fs/cgroup` is the only cgroup mount. Mounting cgroupfs elsewhere is supported but always produces a v2 view of the same kernel state.

Controllers must be explicitly enabled per-subtree via `cgroup.subtree_control`. An application that creates a cgroup and immediately tries to set a limit may find the control file missing if the parent's `subtree_control` did not enable that controller. This is standard v2 semantics — Peios does not relax it.

## File modes and DACLs

cgroupfs files have file modes (the standard rwxr-xr-x) for the benefit of `stat()`-based tools, but the file mode is **cosmetic**. Access decisions are made by the DACL on the cgroup file or directory.

This is the same translation that applies to any Peios filesystem: the file mode is a projection of the DACL for tools that read it, not a separate authority. Linux applications that `chmod` a cgroupfs file see the mode update — and Peios translates the chmod into corresponding DACL changes — but the underlying access control is the DACL.

Linux applications that use the **delegation pattern** (chown a subtree to grant management access) work as expected. The chown updates the cgroup directory's owner; standard inheritance and DACL-from-mode translation produce a DACL that grants the new owner appropriate access. Subsequent `mkdir` and limit-writing operations succeed under the new owner.

What changes: any access decision that would have been made by the kernel's UNIX-permission check is now made by AccessCheck against the DACL. The result is consistent with the file mode in normal cases, and stricter than the file mode when the DACL adds explicit deny ACEs or grants more granular rights than mode bits can express.

## The cgroup namespace

The cgroup namespace virtualizes the path view of `/sys/fs/cgroup` so a process inside the namespace sees its cgroup as `/`, hiding ancestors. This works as it does on Linux, with the path translation happening transparently when the process reads `/proc/<pid>/cgroup` or walks `/sys/fs/cgroup`.

See [Namespaces](../process-silos/namespaces) and the [cgroup namespace section of Linux Compatibility for Process Silos](../process-silos/linux-compatibility) for the full virtualization model.

## The device controller

The device controller is implemented via eBPF programs attached to the cgroup, the v2 mechanism. Linux container runtimes that configure device cgroups by default (Docker, runc, CRI-O) install BPF programs to allow or deny specific devices.

On Peios, the device cgroup BPF check runs **alongside** the standard KACS DACL check on the device file. Both must allow:

| Check | Mechanism |
|---|---|
| KACS DACL on `/dev/<device>` | Standard AccessCheck against the device file's SD |
| Device cgroup BPF program | The v2 device controller's BPF hook on cgroup-attached programs |

The cgroup BPF program returns allow/deny based on the cgroup's policy; KACS returns allow/deny based on the file SD. The result is the intersection — if either denies, the open fails. If both allow, the open proceeds.

This means a Linux container runtime that strips device access via the cgroup gets the strip; KACS DACLs cannot override. Conversely, a permissive cgroup policy cannot grant access that the device file's DACL does not permit.

Native Peios deployments typically use only KACS DACLs and let the cgroup default to permissive (or unconfigured). Linux compat deployments configure both; the intersection is enforced.

## Capability requirements

Linux capabilities map to Peios privileges via [credential projection](../linux-compatibility/credential-projection):

| Linux capability | What it gates on Linux | Peios privilege |
|---|---|---|
| `CAP_SYS_ADMIN` (cgroup subset) | Creating top-level cgroups, some subtree-control writes | `SeCreateResourceGroupPrivilege` |
| `CAP_SYS_RESOURCE` | Bypassing certain resource limits | `SeIncreaseQuotaPrivilege` |
| `CAP_SYS_NICE` | Setting `cpu.weight` and similar priority knobs above defaults | `SeIncreaseBasePriorityPrivilege` |

A process that holds the Linux capability cosmetically but does not hold the corresponding Peios privilege will find the cgroup operation denied. The Peios privilege is what the kernel actually checks.

## What changes for Linux applications

The summary, for unmodified Linux applications:

- **v1 is not supported.** Software pinned to v1 paths must be updated. Most modern software supports v2; configuration may need to be adjusted.
- **File modes are cosmetic.** Access is controlled by the DACL, not the mode. Standard delegation patterns (chown a subtree to grant access) still work because mode changes are translated into DACL changes.
- **The device controller composes with KACS DACLs.** Both must allow. Restrictive cgroup policy is enforced; permissive cgroup policy does not bypass file DACLs.
- **`SeCreateResourceGroupPrivilege` is required for top-level creation.** Service-management workflows already run with this privilege; ad-hoc unprivileged calls fail.

Native Peios applications use the standard filesystem API, set DACLs on cgroup directories with `sd add`, and compose cgroups with [silos](../process-silos/understanding-process-silos) explicitly via service manifests. The Linux compatibility surface is a translation layer for software not yet ported to Peios-native conventions.

## Container runtime compatibility

Linux container runtimes that work without modification:

- **systemd** (when used as init or service manager) — full v2 cgroup integration works as expected
- **Docker / containerd / runc** — set up cgroups under `/sys/fs/cgroup` per container, configure device cgroups via BPF
- **Podman** — same model
- **CRI-O** — same model
- **systemd-nspawn** — composes cgroups with namespaces; both work

What does **not** work:

- Runtimes pinned to v1 (some legacy LXC configurations, very old Docker on cgroup-fs driver). Update to v2 (e.g., `--cgroupfs systemd` or v2-compatible LXC).
- Anything depending on `release_agent` notification — port to inotify on `cgroup.events`.
- v1-only controllers (`net_cls`, `net_prio`, `perf_event` v1) — use nftables, socket priorities, and v2 perf cgroup respectively.
