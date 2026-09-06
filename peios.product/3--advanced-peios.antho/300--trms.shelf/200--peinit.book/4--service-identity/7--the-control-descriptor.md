---
title: The Control Descriptor
description: Shutdown and configuration reload are checked against peinit's own descriptor rather than any service's.
---

Two operations are not about any one service: shutting the system down,
and re-reading the configuration. They are checked against peinit's own
descriptor, stored at `Machine\System\Init\ControlSecurity` as a binary
value. [*svcsd.control-operations-use-peinits-own-descriptor]

## Access rights

| Right | Bit | Grants |
|---|---|---|
| `SYSTEM_SHUTDOWN` | 0x0001 | Initiate poweroff, reboot or halt. [*svcsd.control-shutdown-grants-poweroff-reboot-halt] |
| `SYSTEM_RELOAD_CONFIG` | 0x0002 | Re-read all definitions from the registry. [*svcsd.control-reload-config-grants-a-definition-reread] |

The generic mapping:

| Generic right | Maps to |
|---|---|
| `GENERIC_READ` | nothing [*svcsd.control-generic-read-conveys-nothing] |
| `GENERIC_WRITE` | `SYSTEM_RELOAD_CONFIG` [*svcsd.control-generic-write-is-reload-config] |
| `GENERIC_EXECUTE` | `SYSTEM_SHUTDOWN` [*svcsd.control-generic-execute-is-shutdown] |
| `GENERIC_ALL` | both [*svcsd.control-generic-all-is-both] |

`GENERIC_READ` maps to nothing because there is nothing to read: the
control descriptor governs two actions and no queries. A grant of
`GENERIC_READ` on it is not an error, it simply conveys no access.

## The default [*svcsd.the-control-default-grants-system-and-administrators-both]

Absent a value in the registry, peinit applies:

```
O:SY G:BA D:(A;;0x0003;;;SY)(A;;0x0003;;;BA)
```

SYSTEM and Administrators both get shutdown and reload-config, as they
both get every service right in the ServiceSecurity default (§4.6). An
administrator who can stop services one at a time can already stop the
system, so withholding shutdown would be theatre.

## Loading [*svcsd.controlsecurity-is-loaded-at-phase-2-and-hot-reloaded]

peinit loads the descriptor during Phase 2 boot and hot-reloads it on
registry change notification, on the same path as the service
descriptors. Until it is loaded — during Phase 1 and the early part of
Phase 2 — the built-in default applies, which matters because the
control socket exists from Phase 1 infrastructure setup onwards.
