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
| `Machine\System\Services\<name>\TimerState\` | Subkey for per-trigger timestamps (multi-trigger services). Each value is named by the trigger's schedule string, percent-encoded (§9.1), and holds a REG_QWORD timestamp. | §9.1 |

## Boot configuration

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Boot\MaxParallelStarts` | dword, >0 | 10 | Maximum services starting concurrently during boot. Missing uses default; zero, type mismatch, or malformed payload is invalid boot configuration. | §2.2 |
| `Machine\System\Boot\BootSuccessGrace` | dword | 30 | Seconds every Critical service must hold a dependent-satisfying state (Active/Completed/Skipped) before boot is successful. | §2.3 |
| `Machine\System\Boot\ShutdownTimeout` | dword | 90 | Maximum seconds for the entire graceful shutdown sequence. | §10.1 |

## peinit operational parameters

| Key | Type | Default | Purpose | Defined in |
|---|---|---|---|---|
| `Machine\System\Init\ControlSecurity` | binary | SYSTEM full, Administrators shutdown + reload-config | Security Descriptor for system-level control operations. | §3.4 |
| `Machine\System\Init\MaxControlConnections` | dword | 32 | Maximum concurrent control socket connections. | §11.1 |
| `Machine\System\Init\MaxRequestSize` | dword | 65536 | Maximum control socket request size in bytes. | §11.1 |
| `Machine\System\Init\ConnectionTimeout` | dword | 30 | Seconds before an idle control socket connection is closed. | §11.1 |
| `Machine\System\Init\MaxLogLineLength` | dword | 8192 | Maximum bytes per service output line before truncation. | §12.1 |
| `Machine\System\Init\MaxLogBufferPerService` | dword | 65536 | Maximum bytes buffered per service pipe before backpressure. | §12.1 |
| `Machine\System\Init\EnvVars\` | parent key | empty | Default environment variables injected into Phase 2 services (value name = variable name, REG_SZ data = value). Overrides the compiled-in base. SD is security-critical (write = inject into every service). | §4.1 |
| `Machine\System\Init\ProvisionedPaths\` | parent key | empty | Boot-time path provisioning entries. Each child key describes one directory or file that peinit creates/verifies and secures before Phase 2 starts. | §2.1 |
| `Machine\System\Init\ProvisionedPaths\<name>\Kind` | string | -- | Provisioned path kind: `directory` or `file`. Required on each entry. | §2.1 |
| `Machine\System\Init\ProvisionedPaths\<name>\Path` | string | -- | Absolute filesystem path for the provisioned object. Required on each entry. | §2.1 |
| `Machine\System\Init\ProvisionedPaths\<name>\Security` | binary | built-in default | Peios file security descriptor to apply to the provisioned object. | §2.1 |
| `Machine\System\Init\ProvisionedPaths\<name>\Required` | dword | 0 | If 1, failure to provision the entry enters Recovery mode before Phase 2. | §2.1 |
