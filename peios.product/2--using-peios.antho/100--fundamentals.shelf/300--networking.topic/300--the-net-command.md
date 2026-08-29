---
title: The net command
type: reference
description: net shows what netd made of the network — interfaces, levels, leases — and asks it to renew, reconcile, or wait for a readiness level.
related:
  - peios/networking/overview
  - peios/networking/configuring-profiles
  - peios/services-and-jobs/controlling-services
---

`net` talks to netd over `/run/netd/control.sock`. It shows state and pokes the daemon; it does not change configuration — that is a registry write, and [Configuring profiles](~peios/networking/configuring-profiles) covers it.

## Commands

| Command | Does |
|---|---|
| `net status` | Hostname, the machine's readiness level, and every interface: profile, link state, level, hardware identity, addresses, gateway, DNS, lease. |
| `net wait <level> [seconds]` | Block until the machine reaches `link`, `addressed` or `routed`, or the timeout (default 60) passes. For scripts that need the network. |
| `net renew <interface>` | Renew the DHCP lease now. Accepts a kernel name or an interface id. |
| `net reconcile` | Re-run the reconciler immediately rather than waiting for an event. |
| `net profile list` | The profiles in the registry with their priorities. |

## Reading `net status`

```
hostname  workshop
level     routed

enp0s3  [3f2a…]
  profile   ethernet
  state     up, carrier
  level     routed
  hardware  52:54:00:12:34:56 pci-0000:00:03.0 virtio_net
  address   10.0.2.15/24
  gateway   10.0.2.2
  dns       10.0.2.3
  lease     bound from 10.0.2.2, 86395s left
```

`level` is the readiness level: `absent` (down or no carrier), `link`, `addressed`, `routed`. The machine's level is the highest among managed interfaces. `state` also reports `unmanaged` (the profile has `Managed` off) or `disabled` (`Enabled` is 0 in the inventory).

The bracketed value after the name is the interface id — the inventory key under `Machine\System\Network\Interfaces`.

## Who may run it

The control object is a security descriptor: `Machine\System\Network\ControlSecurity`, or a compiled default when that is unset. `status`, `wait` and `profile list` need `NETWORK_QUERY`, which the default grants to everyone. `renew` and `reconcile` need `NETWORK_CONTROL`, which the default grants to SYSTEM and Administrators. A denied request reports `access denied`.

## Exit status

| Code | Meaning |
|---|---|
| 0 | Done; for `wait`, the level was reached. |
| 1 | netd refused or could not be reached; for `wait`, the timeout passed. |
| 2 | Usage error. |

## See also

- [Networking](~peios/networking/overview)
- [Configuring profiles](~peios/networking/configuring-profiles)
- `regman Machine\System\Network` on the machine, for every key netd reads.
