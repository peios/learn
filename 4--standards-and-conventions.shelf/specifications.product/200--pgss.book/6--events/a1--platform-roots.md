---
title: Platform Roots
description: The short event-type roots reserved to platform components, the component each belongs to, and the package that ships it.
---

The platform roots (§6.3). Every other emitter roots its event types at
its package name. This list is open: a root is added by appending it
under §6.11, and is never reassigned.

| Root | Component | Package |
|---|---|---|
| `kacs` | Kernel Access Control Subsystem | `dev.peios.kernel` |
| `lcs` | The kernel's registry (configuration store) | `dev.peios.kernel` |
| `kmes` | Kernel Mediated Event Subsystem | `dev.peios.kernel` |
| `stratafs` | StrataFS | `dev.peios.kernel` |
| `ntfe` | The kernel's network-policy engine | `dev.peios.kernel` |
| `peinit` | The service manager | `dev.peios.peinit` |
| `peipkg` | The package manager | `dev.peios.peipkg` |
| `eventd` | The event store | `dev.peios.eventd` |
| `authd` | The authentication daemon | `dev.peios.authd` |
| `lpsd` | The local principal source | `dev.peios.authd-lpsd` |
| `timed` | The time daemon | `dev.peios.timed` |
| `netd` | The network daemon | `dev.peios.netd` |
| `trustd` | The trust daemon | `dev.peios.trustd` |

These roots are reserved for components that write no events yet, and
MUST NOT be used by anything else:

| Root | Component |
|---|---|
| `resolvd` | The name-resolution daemon |
| `ud` | The user daemon |
| `loregd` | The log store |

> [!NOTE]
> A root names a component rather than a package because one package
> ships several components with separate concerns: the kernel package
> ships five, and an administrator who wants the access audit without
> the network-policy reports needs `kacs` and `ntfe` to be separate
> policy anchors.
