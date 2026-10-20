---
title: Checking Connectivity
type: how-to
description: Separate link configuration, DNS, listener authority, and packet policy when diagnosing a connection.
---

Network readiness, name resolution, certificate trust, and permission to
connect are separate checks. Preserve the failed command and its diagnostic
before changing configuration.

## Follow the symptom

1. Run `net status` to identify the affected interface, its carrier, rule,
   profile, addresses, and route. Run `resolv status` for the DNS servers
   actually selected.
2. Choose the next check from the table. Use the intended service and host,
   rather than treating any successful probe as proof of full connectivity.
3. If a change is necessary, follow the owning component's procedure with
   a local recovery path. Then repeat the original failed operation.

| Observation | Next check |
|---|---|
| No carrier or readiness `absent` | Link, cable, and the interface verdict. |
| `IGNORE`, `DOWN`, or no profile | `net rules` and the profile-selection policy. |
| Carrier but no offered address | Profile families and `Address.Offered`, server reachability, and DHCP policy. |
| Only a `169.254` address | Link-local fallback; it does not establish a routed lease. |
| Address but no default route | `Route.Offered` or the configured gateway and route-addition diagnostics. |
| IP works but a name fails | `resolv query NAME`, server selection, and not-found versus unavailable. |
| One service fails | Its listener, bind authority, packet policy, and application response. |
| Stored changes do not apply | netd's acceptance and the kernel's packet-policy acceptance separately. |
| TLS verification fails | Expected peer identity, selected trust anchors, and the reported certificate. |

The [profile workflow](~peios/networking/configuring-profiles) and
[resolver guide](~peios/networking/name-resolution) explain their own checks.
For firewall changes, use [Changing Network
Policy](~peios/network-operations/changing-policy).

## Readiness and ownership

Readiness progresses through `absent`, `link`, `addressed`, and `routed`.
An address can be link-local; a default route does not prove Internet, DNS,
or application availability. `net wait` accepts at least its requested
level, while Peinit's declared readiness dependency matches a published
level. Check the [readiness
reference](~peios/advanced-peios/netd/what-netd-publishes/readiness) when
choosing a service dependency.

netd owns addresses on joined interfaces and its tagged routes. Manual
address changes can disappear during reconciliation. It leaves the kernel's
IPv6 link-local address and other programs' route tags alone. `IGNORE` is
not a cleanup request. Restarting netd can interrupt offered configuration
while DHCP and router discovery run again; it is not a harmless reload.

Network `Name` and `Trust` labels are operator policy, not authenticated
proof of the network's identity. Changing them can affect both interface
selection and the firewall. Wireless association requires a supplicant;
netd's profiles do not implement association, and the baseline leaves
wireless unmanaged.

## Compare daemon and network evidence

Inspect captured service output when configuration does not explain a
failure:

```sh
evctl 'LOGS FROM netd SINCE 1h ago TAKE 40'
evctl 'LOGS FROM resolvd SINCE 1h ago TAKE 40'
```

Use `ss -lnt` on the receiving machine to inspect TCP listeners. A targeted
`nc -vz HOST PORT` checks a TCP connection, not application correctness.
`dig @127.0.0.53 NAME A` queries the local DNS stub directly; it does not
change resolver policy. Choose hosts and traffic you are authorized to test.

An absent echo reply does not establish that a host is down. Ordinary echo
uses datagram sockets, while packet capture and some probe modes require
raw-socket authority. Neither installing a diagnostic utility nor selecting
its privileged mode grants native privileges or a firewall exception.

The [network utility compatibility
reference](~peios/compatibility/network-utilities) describes the Peios ports'
file, authority, and supported-mode differences. Tool availability depends
on the installed packages, not this guide.
