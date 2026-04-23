---
title: Registry Key Reference
---

This appendix lists every registry key that peinit reads or writes.
Definitions and semantics are in the sections referenced below.

## Service definitions

| Key | Purpose | Defined in |
|---|---|---|
| `Machine\System\Services\` | Parent key for all service definitions. Each child key is a service. | Service Model: Definition Schema |
| `Machine\System\Services\SchemaVersion` | Schema version guard (dword, currently 1). | Service Model: Definition Schema |
| `Machine\System\Services\<name>\LastTimerRun` | Last-run timestamp for persistent timers (single-trigger services). REG_QWORD. Written by peinit. | Timers |
| `Machine\System\Services\<name>\TimerState\` | Subkey for per-trigger timestamps (multi-trigger services). Each value is named by the trigger's schedule string and holds a REG_QWORD timestamp. | Timers |

## Boot configuration

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Boot\Mounts\` | parent key | -- | Mount entries. Each child generates a mount pseudo-service. | Phase 2 |
| `Machine\System\Boot\MaxParallelStarts` | dword | 10 | Maximum services starting concurrently during boot. | Phase 2 |
| `Machine\System\Boot\BootSuccessGrace` | dword | 30 | Seconds all Critical services must remain Active before boot is successful. | Boot Modes |
| `Machine\System\Boot\ShutdownTimeout` | dword | 90 | Maximum seconds for the entire graceful shutdown sequence. | Shutdown |
| `Machine\System\Boot\RootStorage\` | parent key | -- | Root storage configuration. Read by the initramfs, not by peinit directly. | Bootstrap |

## peinit operational parameters

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Init\ControlSecurity` | binary | SYSTEM full, Administrators shutdown + reload-config | Security Descriptor for system-level control operations. | Service Model: Service Security |
| `Machine\System\Init\MaxControlConnections` | dword | 32 | Maximum concurrent control socket connections. | Control Interface: Protocol |
| `Machine\System\Init\MaxRequestSize` | dword | 65536 | Maximum control socket request size in bytes. | Control Interface: Protocol |
| `Machine\System\Init\ConnectionTimeout` | dword | 30 | Seconds before an idle control socket connection is closed. | Control Interface: Protocol |
| `Machine\System\Init\MaxLogLineLength` | dword | 8192 | Maximum bytes per service output line before truncation. | Service Output Handling |
| `Machine\System\Init\MaxLogBufferPerService` | dword | 65536 | Maximum bytes buffered per service pipe before backpressure. | Service Output Handling |
