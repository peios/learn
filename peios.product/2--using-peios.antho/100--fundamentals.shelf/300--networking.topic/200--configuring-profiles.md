---
title: Configuring profiles
type: how-to
description: Write a profile and an interface-layer rule in the registry — pick the interfaces, say what to take from the network and what to dictate — and watch netd apply it live.
related:
  - peios/networking/overview
  - peios/networking/network-policy-reference
  - peios/networking/the-net-command
  - peios/registry-administration/regman
  - peios/registry-concepts/keys-values-and-types
---

Network configuration is two kinds of key under `Machine\System\Network`. A **profile**, a subkey of `Profiles`, says how an interface stands on a network: what to take from the network's offer and what to dictate. A **rule**, a subkey of `Rules\Interface`, says which interfaces stand in which profile. netd watches the subtree, so a change takes effect within a moment of the write — no restart, no reload command.

Every value is documented on the machine, `regman Machine\System\Network`, and in the [reference](~peios/networking/network-policy-reference).

## See what you have

```
net status
net rules
net profiles
```

`net status` shows each interface with its verdict: the rule that spoke and the profile it stands in. An image's baseline is a profile `default` that takes the network's address, way out and name servers, and a rule `wired` that puts every wired interface in it at priority 10.

## A static address

Two keys. First a profile that says only what differs from `default`, as a subkey of it, so everything else — the name servers from the network, the link-local fallback — is inherited:

```
reg new Machine/System/Network/Profiles/default/db1
reg set Machine/System/Network/Profiles/default/db1 Address.Offered dword:0
reg set Machine/System/Network/Profiles/default/db1 Address.Static multi:10.0.0.5/24
reg set Machine/System/Network/Profiles/default/db1 Route.Offered dword:0
reg set Machine/System/Network/Profiles/default/db1 Route.Gateway 10.0.0.1
```

Then a rule naming the interface by its bus path (from `net status`, stable across boots), as an exception under the baseline's `wired` rule so it is judged only for wired interfaces:

```
reg new Machine/System/Network/Rules/Interface/wired/db1
reg set Machine/System/Network/Rules/Interface/wired/db1 Interface.Path.Equal pci-0000:00:03.0
reg set Machine/System/Network/Rules/Interface/wired/db1 Actions multi:JOIN(default/db1)
```

The exception is more specific than `wired`, so it speaks for that interface and DHCP stops. `net status` shows `JOIN(default/db1) by wired/db1` and `readiness routed` once the default route is in place. To pin the name servers as well, add `Dns.Offered = 0` and `Dns.Servers` to the profile.

## Facts a rule can name

Every `<Fact>.<Operator>` value present must hold. Comparison is exact; `Equal` takes a list for *any of*.

| Fact | Matches | Example |
|---|---|---|
| `Interface` | the kernel's interface name | `enp0s3` |
| `Interface.Kind` | `wired`, `wireless`, `loopback`, `other` | `wired` |
| `Interface.Id` | the stable id from `net status` | `3f2a1b8e-…` |
| `Interface.Mac` | the hardware address | `52:54:00:12:34:56` |
| `Interface.Path` | the bus path | `pci-0000:00:03.0` |
| `Interface.Driver` | the kernel driver | `virtio_net` |
| `Network.Name` | the `Name` you gave the network's record | `palfrey-home` |
| `Network.Trust` | the `Trust` you gave it | `corporate` |

Prefer `Interface.Path` or `Interface.Id` for a specific card and `Interface.Kind` or `Interface.Driver` for a class. `Interface` (the name) is the least stable: the kernel may call the same card something else after a hardware change. A fact the interface lacks — a tunnel has no `Path` — makes the condition false, never an error.

## Taking the offer, with adjustments

`default` believes the network about the address, the way out and the name servers. To keep the address but pin DNS, override two values in a derived profile and point a rule at it — or, if the whole machine should behave so, edit `default` itself:

```
reg set Machine/System/Network/Profiles/default Dns.Offered dword:0
reg set Machine/System/Network/Profiles/default Dns.Servers multi:1.1.1.1,9.9.9.9
```

Two more `Dns` values decide *which* names an interface's servers are asked for, which matters the moment a second interface appears — typically a VPN:

```
reg set Machine/System/Network/Profiles/vpn Dns.Domains multi:corp.example
reg set Machine/System/Network/Profiles/vpn Dns.Default dword:1
reg set Machine/System/Network/Profiles/vpn Dns.Exclusive dword:1
```

`Dns.Domains` sends names under `corp.example` to this interface's servers. `Dns.Default` sends *every other* name there too (unset, an interface claims that only when it carries the default route). `Dns.Exclusive` goes further: while this interface is up, no other interface's servers are consulted for anything — the "ultimate protection" a VPN wants, and the setting that stops a hostile LAN from advertising the VPN's own domain. See [name resolution](~peios/networking/name-resolution).

To hold an offered address across a server outage:

```
reg set Machine/System/Network/Profiles/default Address.OnExpiry Keep
```

`Keep` trades the risk of an address conflict for continuity; the default `Drop` is the safe choice.

## IPv6

`Address.Offered` covers both families: on a network with router advertisements the interface gets a stable-privacy address per advertised prefix, and with `Route.Offered` and `Dns.Offered` the advertised default route and DNS from RDNSS or stateless DHCPv6. Three values change that:

```
reg set Machine/System/Network/Profiles/office Address.Families multi:ipv4
reg set Machine/System/Network/Profiles/laptop Address.Temporary dword:1
reg set Machine/System/Network/Profiles/office Route.Gateway multi:10.0.0.1,fe80::1
```

`Address.Families = ipv4` stops router discovery on interfaces in the profile and drops IPv6 entries from `Address.Static`. `Address.Temporary` adds daily-rotating temporary addresses beside the stable one, for machines whose traffic should not correlate over days; the stable address remains for inbound. An IPv6 entry in `Route.Gateway` — usually a link-local address — pins the default router instead of believing advertisements.

The stable address is a keyed digest of the prefix and the interface's identity, not the MAC: it survives reboots and reinstalls that keep `/var/state/netd`, and a different network sees a different, unlinkable address.

## Prefer a cable over WiFi

Both interfaces get a default route; the metric decides which is used. Wired defaults to 100 and wireless to 600, so no configuration is needed. To invert it, set `Route.Metric` on the profiles.

## Name a network, and behave differently on it

Once an interface has stood on a network, `net status` shows the record's id. Give it a name and your word on it:

```
reg set Machine/System/Network/Networks/<id> Name palfrey-home
reg set Machine/System/Network/Networks/<id> Trust home
```

Then a rule can choose the profile by the network rather than the interface — the laptop case, one radio with a different profile at home, in the office and anywhere else:

```
reg new Machine/System/Network/Rules/Interface/radio
reg set Machine/System/Network/Rules/Interface/radio Interface.Kind.Equal wireless
reg set Machine/System/Network/Rules/Interface/radio Actions multi:JOIN(untrusted)
reg new Machine/System/Network/Rules/Interface/radio/home
reg set Machine/System/Network/Rules/Interface/radio/home Network.Name.Equal palfrey-home
reg set Machine/System/Network/Rules/Interface/radio/home Actions multi:JOIN(home)
```

Until a network has been identified on the link, the `Network.*` facts are absent, so the radio stands in `untrusted` first and moves to `home` once the network is known. `Trust` is your word until PNP's trust pass gives it evidence: a rule that conditions on it is stating that you accept the identification.

## Hand an interface to something else

An `IGNORE` verdict means netd never touches a matched interface — no addresses, no routes, no link changes, no DHCP:

```
reg new Machine/System/Network/Rules/Interface/leave-alone
reg set Machine/System/Network/Rules/Interface/leave-alone Interface.Equal tap0
reg set Machine/System/Network/Rules/Interface/leave-alone Actions multi:IGNORE
```

## Take an interface down

A `DOWN` verdict keeps a matched interface administratively down, whatever other rules say — `DOWN` is the strictest verdict, and the priority makes sure nothing outranks it:

```
reg new Machine/System/Network/Rules/Interface/dead-card
reg set Machine/System/Network/Rules/Interface/dead-card Interface.Id.Equal <id>
reg set Machine/System/Network/Rules/Interface/dead-card Priority dword:100
reg set Machine/System/Network/Rules/Interface/dead-card Actions multi:DOWN
```

The interface id is in `net status`. Delete the rule, or set `Enabled = 0` on it, to bring the interface back.

## Ask for the same address

The address a network last leased is on its record, and netd asks for it first. Write it yourself for a soft reservation — a request the server may refuse, unlike a static address:

```
reg set Machine/System/Network/Networks/<id> RequestedAddress 10.0.2.50
```

## Set the hostname

```
reg set Machine/System/Network Hostname workshop
```

netd applies it on the next pass. A profile with `Hostname.Offered` on adopts a network-supplied name when this value is unset; `Hostname.Announce` tells DHCP servers the name so their DNS can register it. Both are off in a bare profile.

## When netd refuses

A rule with an unknown fact, a `JOIN` naming a profile that does not exist, a profile with an unknown value, or two rules tied on priority naming different profiles for one interface refuses the whole generation: netd keeps the last good one and `net status` says why, as a `policy REFUSED` line. A `JOIN` of a profile that exists but has `Enabled = 0` is not a fault — that rule abstains and its parent, another rule or the backstop answers.

## Where to go next

- [The net command](~peios/networking/the-net-command) — read back what netd did.
- [Networking](~peios/networking/overview) — the model behind these keys.
- [Network policy reference](~peios/networking/network-policy-reference) — every fact, verdict and profile value.
