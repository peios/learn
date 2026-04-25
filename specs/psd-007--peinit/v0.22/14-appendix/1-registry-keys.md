---
title: Registry Key Reference
---

This appendix lists every registry key that peinit reads or writes.
Definitions and semantics are in the sections referenced below.

## Service definitions

| Key | Purpose | Defined in |
|---|---|---|
| `Machine\System\Services\` | Parent key for all service definitions. Each child key is a service. | §3.2 |
| `Machine\System\Services\SchemaVersion` | Schema version guard (dword, currently 1). | §3.2 |
| `Machine\System\Services\<name>\LastTimerRun` | Last-run timestamp for persistent timers (single-trigger services). REG_QWORD. Written by peinit. | §9.1 |
| `Machine\System\Services\<name>\TimerState\` | Subkey for per-trigger timestamps (multi-trigger services). Each value is named by the trigger's schedule string and holds a REG_QWORD timestamp. | §9.1 |

## Boot configuration

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Boot\Mounts\` | parent key | -- | Mount entries. Each child generates a mount pseudo-service. | §2.2 |
| `Machine\System\Boot\MaxParallelStarts` | dword | 10 | Maximum services starting concurrently during boot. | §2.2 |
| `Machine\System\Boot\BootSuccessGrace` | dword | 30 | Seconds all Critical services must remain Active before boot is successful. | §2.3 |
| `Machine\System\Boot\ShutdownTimeout` | dword | 90 | Maximum seconds for the entire graceful shutdown sequence. | §10.1 |
| `Machine\System\Boot\RootStorage\` | parent key | -- | Root storage configuration. Read by the initramfs, not by peinit directly. | §2.1 |

## peinit operational parameters

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Init\ControlSecurity` | binary | SYSTEM full, Administrators shutdown + reload-config | Security Descriptor for system-level control operations. | §3.4 |
| `Machine\System\Init\MaxControlConnections` | dword | 32 | Maximum concurrent control socket connections. | §11.1 |
| `Machine\System\Init\MaxRequestSize` | dword | 65536 | Maximum control socket request size in bytes. | §11.1 |
| `Machine\System\Init\ConnectionTimeout` | dword | 30 | Seconds before an idle control socket connection is closed. | §11.1 |
| `Machine\System\Init\MaxLogLineLength` | dword | 8192 | Maximum bytes per service output line before truncation. | §12.1 |
| `Machine\System\Init\MaxLogBufferPerService` | dword | 65536 | Maximum bytes buffered per service pipe before backpressure. | §12.1 |
