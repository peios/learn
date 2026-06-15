---
title: Service Security
---

Each service has two independent Security Descriptors. This section
defines both and the access rights they control.

## Registry key SD

The registry key at `Machine\System\Services\<name>` has its own
SD, inherited from the parent key or set explicitly. This SD
controls who can read and write the service definition in the
registry. It is enforced by LCS via AccessCheck at key open time.

The registry key SD is not peinit's concern -- it is a registry-
level access control mechanism. peinit reads service definitions
as SYSTEM, which has full access.

## ServiceSecurity SD

The ServiceSecurity SD controls who can perform runtime operations
on the service via peinit's control interface. It is stored as a
binary value (`ServiceSecurity`) on the service's registry key but
enforced by peinit, not by LCS.

If ServiceSecurity is absent, the service inherits its parent key's
ServiceSecurity. If no ancestor has a ServiceSecurity value, peinit
MUST apply a default SD that grants SYSTEM full access and
Administrators (`S-1-5-32-544`) query and stop rights.

### Service access rights

| Right | Bit | Grants |
|---|---|---|
| SERVICE_QUERY_STATUS | 0x0001 | Query service state, PID, cause, health, warnings. |
| SERVICE_START | 0x0002 | Start the service. |
| SERVICE_STOP | 0x0004 | Stop the service. |
| SERVICE_INTERROGATE | 0x0008 | Reload the service. |
| SERVICE_ALL_ACCESS | 0x000F | The union of all rights above. This is the "full access" granted to SYSTEM in the default SD. |

Restart requires both SERVICE_STOP and SERVICE_START.

### ServiceSecurity GenericMapping

When peinit calls AccessCheck for a ServiceSecurity SD, it MUST use the
following GenericMapping:

| Generic right | Maps to |
|---|---|
| GENERIC_READ | SERVICE_QUERY_STATUS |
| GENERIC_WRITE | SERVICE_START \| SERVICE_STOP \| SERVICE_INTERROGATE |
| GENERIC_EXECUTE | SERVICE_START \| SERVICE_STOP \| SERVICE_INTERROGATE |
| GENERIC_ALL | SERVICE_ALL_ACCESS |

When a client sends a control command via the control socket,
peinit MUST:

1. Obtain the caller's token via `kacs_open_peer_token`.
2. Resolve the target service and its ServiceSecurity SD. If the
   command names no service definition and no definition-removed
   runtime entry that this specification keeps addressable, peinit
   MUST return `UNKNOWN_SERVICE` and MUST NOT invent a synthetic SD.
3. Call AccessCheck with the caller's token against the target
   service's ServiceSecurity SD.
4. If AccessCheck denies the requested access: return an
   ACCESS_DENIED error and log the attempt (caller SID, target
   service, requested right).
5. If AccessCheck grants the requested access: proceed with the
   command.

### ServiceSecurity hot-reload

ServiceSecurity is hot-reloaded. Changes to the ServiceSecurity
value in the registry take effect on the next control request
without requiring a service restart. peinit MUST pick up
ServiceSecurity changes via registry change notifications.

## peinit control SD

System-level operations (shutdown, reload-config) are not
per-service -- they are checked against peinit's own SD, stored at
`Machine\System\Init\ControlSecurity` (binary).

peinit MUST load this SD during Phase 2 boot and hot-reload it on
registry change notifications.

### System access rights

| Right | Bit | Grants |
|---|---|---|
| SYSTEM_SHUTDOWN | 0x0001 | Initiate shutdown (poweroff, reboot, halt). |
| SYSTEM_RELOAD_CONFIG | 0x0002 | Re-read all service definitions from the registry. |

### ControlSecurity GenericMapping

When peinit calls AccessCheck for the peinit ControlSecurity SD, it MUST use
the following GenericMapping:

| Generic right | Maps to |
|---|---|
| GENERIC_READ | 0 |
| GENERIC_WRITE | SYSTEM_RELOAD_CONFIG |
| GENERIC_EXECUTE | SYSTEM_SHUTDOWN |
| GENERIC_ALL | SYSTEM_SHUTDOWN \| SYSTEM_RELOAD_CONFIG |

The default ControlSecurity SD MUST grant:

- SYSTEM (`S-1-5-18`): full access.
- Administrators (`S-1-5-32-544`): SYSTEM_SHUTDOWN and
  SYSTEM_RELOAD_CONFIG.

## Independence of SDs

The registry key SD and ServiceSecurity SD are independent. An
administrator might have permission to query a service's status
(ServiceSecurity grants SERVICE_QUERY_STATUS) but not to read its
configuration (registry key SD denies READ). Or vice versa. Both
combinations are valid -- runtime control and configuration access
are independent concerns.

## The list command

The `list` command returns all services and their states. peinit
MUST filter the result: only services for which the caller has
SERVICE_QUERY_STATUS are included. A caller with no service query
rights sees an empty list.
