---
title: Configuring profiles
type: how-to
description: Write a network profile in the registry — match an interface, give it DHCP or a static address, set DNS — and watch netd apply it live.
related:
  - peios/networking/overview
  - peios/networking/the-net-command
  - peios/registry-administration/regman
  - peios/registry-concepts/keys-values-and-types
---

A profile is a subkey of `Machine\System\Network\Profiles`. Its `Match` subkey says which interfaces it claims; `Address` and `DNS` say what to do with them. netd watches the subtree, so a change takes effect within a moment of the write — no restart, no reload command.

Every key and value is documented on the machine: `regman Machine\System\Network\Profiles`.

## See what you have

```
net status
net profile list
reg ls Machine/System/Network/Profiles
```

`net status` shows each interface with the profile that claimed it. An image's default profile, `ethernet`, claims every Ethernet interface for DHCP at priority 10.

## A static address

Claim the interface by its bus path (from `net status`, stable across boots) and give it an address and gateway:

```
reg new Machine/System/Network/Profiles/office
reg set Machine/System/Network/Profiles/office Priority dword:100
reg new Machine/System/Network/Profiles/office/Match
reg set Machine/System/Network/Profiles/office/Match Path pci-0000:00:03.0
reg new Machine/System/Network/Profiles/office/Address
reg set Machine/System/Network/Profiles/office/Address DHCP4 dword:0
reg set Machine/System/Network/Profiles/office/Address Static multi:10.0.0.5/24
reg set Machine/System/Network/Profiles/office/Address Gateway 10.0.0.1
reg new Machine/System/Network/Profiles/office/DNS
reg set Machine/System/Network/Profiles/office/DNS Servers multi:10.0.0.1
```

Priority 100 outranks the default profile's 10, so `office` wins for that interface and DHCP stops. `net status` shows the new address and `level routed` once the default route is in place.

## Match keys

Every value present under `Match` must hold; a profile with no match keys matches nothing. Comparison ignores case and allows one `*`.

| Value | Matches | Example |
|---|---|---|
| `Name` | the kernel's interface name | `enp*` |
| `MAC` | the hardware address | `52:54:00:*` |
| `Path` | the bus path from the inventory | `pci-0000:00:03.0` |
| `Driver` | the kernel driver | `virtio_net` |
| `Type` | `ether`, `wlan`, `loopback`, `other` | `ether` |

Prefer `Path` or `MAC` for a specific machine and `Type` or `Driver` for a class. `Name` is the least stable: the kernel may call the same card something else after a hardware change.

## DHCP with adjustments

The default profile is DHCP with everything from the lease. To keep DHCP but pin DNS, or to hold the address across an outage:

```
reg set Machine/System/Network/Profiles/ethernet/DNS UseFromDHCP dword:0
reg set Machine/System/Network/Profiles/ethernet/DNS Servers multi:1.1.1.1,9.9.9.9
```

Two more `DNS` values decide *which* names an interface's servers are
asked for, which matters the moment a second interface appears —
typically a VPN:

```
reg set Machine/System/Network/Profiles/vpn/DNS SearchDomains multi:corp.example
reg set Machine/System/Network/Profiles/vpn/DNS DNSDefaultRoute dword:1
reg set Machine/System/Network/Profiles/vpn/DNS DNSExclusive dword:1
```

`SearchDomains` sends names under `corp.example` to this interface's
servers. `DNSDefaultRoute` sends *every other* name there too (unset, an
interface claims that only when it carries the default route).
`DNSExclusive` goes further: while this interface is up, no other
interface's servers are consulted for anything — the "ultimate
protection" a VPN wants, and the setting that stops a hostile LAN from
advertising the VPN's own domain. See [name resolution](~peios/networking/name-resolution).

To hold a DHCP address across a server outage:

```
reg set Machine/System/Network/Profiles/ethernet/Address OnLeaseExpiry Keep
```

`OnLeaseExpiry Keep` trades the risk of an address conflict for continuity; the default `Drop` is the safe choice.

## IPv6

On by default, nothing to configure: on a network with router advertisements the interface gets a stable-privacy address per advertised prefix, the advertised default route, and DNS from RDNSS or stateless DHCPv6. Three values change that:

```
reg set Machine/System/Network/Profiles/office/Address IPv6 dword:0
reg set Machine/System/Network/Profiles/laptop/Address IPv6Temporary dword:1
reg set Machine/System/Network/Profiles/office/Address Gateway6 fe80::1
```

`IPv6` off stops router discovery on matched interfaces — static IPv6 addresses in `Static` (e.g. `fd00::5/64`) still apply. `IPv6Temporary` adds daily-rotating temporary addresses beside the stable one, for machines whose traffic should not correlate over days; the stable address remains for inbound. `Gateway6` pins the default router — usually a link-local address — instead of believing advertisements.

The stable address is a keyed digest of the prefix and the interface's identity, not the MAC: it survives reboots and reinstalls that keep `/var/state/netd`, and a different network sees a different, unlinkable address.

## Prefer a cable over WiFi

Both interfaces get a default route; the metric decides which is used. Wired defaults to 100 and wireless to 600, so no configuration is needed. To invert it, set `RouteMetric` on the profiles.

## Hand an interface to something else

`Managed` off means netd never touches a matched interface — no addresses, no routes, no link changes, no DHCP:

```
reg new Machine/System/Network/Profiles/leave-alone
reg set Machine/System/Network/Profiles/leave-alone Priority dword:200
reg new Machine/System/Network/Profiles/leave-alone/Match
reg set Machine/System/Network/Profiles/leave-alone/Match Name tap0
reg set Machine/System/Network/Profiles/leave-alone Managed dword:0
```

## Take an interface down

`Enabled` in the inventory is the persistent switch, independent of the profile:

```
reg set Machine/System/Network/Interfaces/<ifid> Enabled dword:0
```

The interface id is in `net status`. Set it back to 1 to bring the interface up again.

## Set the hostname

```
reg set Machine/System/Network Hostname workshop
```

netd applies it on the next pass. A profile with `AcceptHostname` on adopts a DHCP-supplied name when this value is unset.

## Where to go next

- [The net command](~peios/networking/the-net-command) — read back what netd did.
- [Networking](~peios/networking/overview) — the model behind these keys.
