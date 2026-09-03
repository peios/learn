---
title: The net command
type: reference
description: net shows what netd made of the network — interfaces, verdicts, readiness, leases — lists the interface layer's rules and profiles, and asks netd to renew, reconcile, or wait for a readiness level.
related:
  - peios/networking/overview
  - peios/networking/configuring-profiles
  - peios/services-and-jobs/controlling-services
---

`net` talks to netd over `/run/netd/control.sock`. It shows state and pokes the daemon; it does not change configuration — that is a registry write, and [Configuring profiles](~peios/networking/configuring-profiles) covers it.

## Commands

| Command | Does |
|---|---|
| `net status` | Hostname, the machine's readiness, whether the newest generation was refused, and every interface: verdict with the rule and profile behind it, link state, readiness, hardware identity, the network identified on it, addresses, gateway, DNS, lease, warnings. |
| `net wait <level> [seconds]` | Block until the machine reaches `link`, `addressed` or `routed`, or the timeout (default 60) passes. For scripts that need the network. |
| `net renew <interface>` | Renew the DHCP lease now. Accepts a kernel name or an interface id. |
| `net reconcile` | Re-run the reconciler immediately rather than waiting for an event. |
| `net rules` | The interface layer, one rule per line: path, priority, conditions, actions. |
| `net profiles` | The profile tree, one profile per line with the values it sets itself. |

## Reading `net status`

```
hostname   workshop
readiness  routed

enp0s3  [3f2a1b8e-…]
  verdict    JOIN(default) by wired
  state      up, carrier
  readiness  routed
  hardware   52:54:00:12:34:56 pci-0000:00:03.0 virtio_net
  network    palfrey-home [9c0d4e21-…] trust home
  address    10.0.2.15/24
  gateway    10.0.2.2
  dns        10.0.2.3
  lease      bound from 10.0.2.2, 86395s left
```

`verdict` is what the interface layer said and who said it: the verdict, the profile (for `JOIN`), and the rule path that spoke — `backstop` when no rule did. `readiness` is `absent` (down or no carrier), `link`, `addressed` or `routed`, shown for joined interfaces; the machine's is the highest among them. `network` is the record under `Machine\System\Network\Networks` identified on the link, with the `Name` and `Trust` you gave it.

The bracketed value after the name is the interface id — the inventory key under `Machine\System\Network\Interfaces`.

A `warning` line reports something the operator should see: discovery went unanswered, or two rules tied and the interface is ignored. A `policy REFUSED:` line at the top means the newest generation could not be built and the last good one stands; it says why.

## Who may run it

The control object is a security descriptor: `Machine\System\Network\ControlSecurity`, or a compiled default when that is unset. `status` and `wait` need `NETWORK_QUERY`, which the default grants to everyone. `renew` and `reconcile` need `NETWORK_CONTROL`, which the default grants to SYSTEM and Administrators. `rules` and `profiles` read the registry directly and need only read access to it. A denied request reports `access denied`.

## Exit status

| Code | Meaning |
|---|---|
| 0 | Done; for `wait`, the level was reached. |
| 1 | netd refused or could not be reached; for `wait`, the timeout passed. |
| 2 | Usage error. |

## See also

- [Networking](~peios/networking/overview)
- [Configuring profiles](~peios/networking/configuring-profiles)
- `regman Machine\System\Network` on the machine, for every key netd reads and writes.
