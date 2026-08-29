---
title: Who can manage a service
type: concept
description: Every control command runs AccessCheck against the service's ServiceSecurity descriptor. The rights, the defaults, and the system control descriptor.
related:
  - peios/services-and-jobs/identity-and-privileges
  - peios/services-and-jobs/controlling-services
  - peios/security-descriptors/overview
  - peios/access-decisions/overview
  - peios/registry-security/access-control
---

A service is a *securable object*. Just as a [file](~peios/file-access/overview) or a [registry key](~peios/registry-security/access-control) carries a [security descriptor](~peios/security-descriptors/overview) that decides who may touch it, a service carries one that decides who may **start, stop, query, or reload** it. peinit enforces it on *every* [control command](~peios/services-and-jobs/controlling-services) — there is no command that skips the check.

This is the second, independent half of the security model. The first half, [Service identity and privileges](~peios/services-and-jobs/identity-and-privileges), is about what a service *can do* (its token). This page is about who can *manage the service* — a completely separate question, answered by a completely separate descriptor.

## Two descriptors, two questions

A service is associated with **two** descriptors that are easy to conflate but answer different questions and are enforced by different components:

| Descriptor | Question | Stored | Enforced by |
|---|---|---|---|
| **Registry key SD** | Who can *read or edit the definition*? | On the `Machine\System\Services\<name>` key | [LCS](~peios/registry-security/access-control), at key-open time |
| **ServiceSecurity SD** | Who can *manage the running service*? | As the `ServiceSecurity` binary value on that key | **peinit**, on every control command |

The registry key SD is ordinary [registry access control](~peios/registry-security/access-control) and not peinit's concern — peinit reads definitions as SYSTEM, which has full access. The **ServiceSecurity** SD is peinit's domain, and the rest of this page is about it.

They are genuinely independent. An administrator might be able to *query a service's status* (ServiceSecurity grants `SERVICE_QUERY_STATUS`) but not *read its configuration* (the registry key SD denies read) — or the reverse. Runtime control and configuration access are separate concerns, and both combinations are valid.

## Service access rights

The ServiceSecurity descriptor grants these rights:

| Right | Bit | Grants |
|---|---|---|
| `SERVICE_QUERY_STATUS` | 0x0001 | Query state, PID, cause, health, warnings. |
| `SERVICE_START` | 0x0002 | Start the service. |
| `SERVICE_STOP` | 0x0004 | Stop the service. |
| `SERVICE_INTERROGATE` | 0x0008 | Reload the service. |
| `SERVICE_ALL_ACCESS` | 0x000F | All of the above — the "full access" granted to SYSTEM by default. |

`restart` requires **both** `SERVICE_STOP` and `SERVICE_START`, since it is a stop followed by a start. `reset` requires `SERVICE_STOP`.

When peinit evaluates the descriptor it maps the generic rights as follows, so a descriptor written with generic rights behaves sensibly:

| Generic | Maps to |
|---|---|
| `GENERIC_READ` | `SERVICE_QUERY_STATUS` |
| `GENERIC_WRITE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_EXECUTE` | `SERVICE_START` \| `SERVICE_STOP` \| `SERVICE_INTERROGATE` |
| `GENERIC_ALL` | `SERVICE_ALL_ACCESS` |

## How a command is authorised

Every control command runs the same gate:

1. peinit captures the caller's [token](~peios/services-and-jobs/identity-and-privileges) from the kernel (the `KACS_SO_PEER_TOKEN` socket option) — the caller's *effective* identity at connection time, so if the caller is [impersonating](~peios/impersonation/overview), the impersonated identity is what is checked.
2. peinit resolves the target service and its ServiceSecurity descriptor.
3. peinit runs [AccessCheck](~peios/access-decisions/overview): the caller's token against the descriptor, for the right the command needs.
4. **Denied** → return `ACCESS_DENIED` and **log the attempt** (caller SID, target service, requested right).
5. **Granted** → execute the command.

> [!NOTE]
> Access denials are always logged — caller, target, and the right requested. Silent denial is a specification violation. If you are debugging a denial, the audit record has everything you need; see [Debugging a denial](~peios/access-decisions/debugging-a-denial).

## The default descriptor

If a service has no `ServiceSecurity` value, it **inherits** its parent key's. If no ancestor sets one either, peinit applies a built-in default:

- **SYSTEM** (`S-1-5-18`) — full access.
- **Administrators** (`S-1-5-32-544`) — query and stop only.

So out of the box, administrators can see and stop a service but not start or reload it unless a descriptor grants more — a conservative default that you widen deliberately.

ServiceSecurity is **hot-reloaded**: a change to the value in the registry takes effect on the **next control request**, with no service restart. peinit picks the change up through a [registry notification](~peios/registry-concepts/watches). This is why ServiceSecurity is in its own [mutability class](~peios/services-and-jobs/defining-a-service) — access policy should be able to change without disturbing a running service.

## The system control descriptor

Some operations are not about any one service — `shutdown` and `reload-config` act on the whole system. These are checked against **peinit's own** descriptor, stored at `Machine\System\Init\ControlSecurity`:

| Right | Bit | Grants |
|---|---|---|
| `SYSTEM_SHUTDOWN` | 0x0001 | Initiate poweroff, reboot, or halt. |
| `SYSTEM_RELOAD_CONFIG` | 0x0002 | Re-read all definitions and rebuild the graph. |

Its generic mapping deliberately gives `GENERIC_READ` *nothing* — there is no "read" of the system control object, only the two actions:

| Generic | Maps to |
|---|---|
| `GENERIC_READ` | (nothing) |
| `GENERIC_WRITE` | `SYSTEM_RELOAD_CONFIG` |
| `GENERIC_EXECUTE` | `SYSTEM_SHUTDOWN` |
| `GENERIC_ALL` | `SYSTEM_SHUTDOWN` \| `SYSTEM_RELOAD_CONFIG` |

The default grants **SYSTEM** full access and **Administrators** both rights. peinit loads this descriptor at boot and hot-reloads it on registry change, exactly like ServiceSecurity.

## Jobs have descriptors too

A [submitted job](~peios/services-and-jobs/jobs-and-operations) is a securable object in the same way. It carries its own descriptor from the moment it exists — by default owned by the submitter and granting `JOB_QUERY`, `JOB_STOP`, and `JOB_SIGNAL` to the submitter, SYSTEM, and Administrators, and *nothing* to the identity the job runs as — and every job command, on either socket, is checked against it. The one thing no descriptor inside peinit governs is who may *submit*: that is the file descriptor on the jobs socket, checked by the kernel when a process connects.

## The list command filters, it does not deny

`list` is access-control-aware in a quieter way: it returns only the services the caller has `SERVICE_QUERY_STATUS` on, and simply **omits** the rest. A caller with no query rights gets an empty list, not a denial. This means a low-privilege principal cannot even enumerate the services it cannot see — the existence of a service is itself information the descriptor controls.

## The boundaries that hold

A few invariants are worth stating outright, because they are what make this trustworthy:

- **peinit never bypasses AccessCheck for a control operation.** No backdoor, no override flag, no "trust localhost."
- **The descriptors are the only policy inputs.** peinit consults the ServiceSecurity and ControlSecurity descriptors and nothing else — not config files, not environment variables, not hardcoded lists.
- **One service's state is never exposed to another without a check.** `status` is per-service access-controlled; `list` filters. The same holds for jobs: `job status` is checked, `job list` filters.

## Where to start

For the *other* half of the security model — what a service can reach once it is running — read [Service identity and privileges](~peios/services-and-jobs/identity-and-privileges).

For the commands these rights gate, read [Controlling services](~peios/services-and-jobs/controlling-services).

For the descriptor and AccessCheck machinery itself, read [Security descriptors](~peios/security-descriptors/overview) and [Access decisions](~peios/access-decisions/overview).
