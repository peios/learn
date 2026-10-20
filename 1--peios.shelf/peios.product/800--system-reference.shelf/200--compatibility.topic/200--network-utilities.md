---
title: Network Utility Compatibility
type: reference
description: Native authority, output protection, and supported-mode boundaries of Peios network utility ports.
---

These contracts describe the Peios package recipes, not a promise that every
image contains each utility. Use the installed manual for exact options.
Begin diagnosis with [Checking Connectivity](~peios/network-operations/checking-connectivity).
The tools retain the invoking native token; installing one grants no extra
privilege, port reservation, or packet-policy exception.

## Probe and inspect

| Tool | Purpose | Boundary |
|---|---|---|
| `ping` | ICMP echo | Ordinary IPv4/IPv6 echo uses datagram sockets; raw modes have separate authority checks. |
| `tracepath`, `traceroute`, `mtr` | Route, path MTU, and latency evidence | Ordinary UDP and echo-datagram modes need no raw-socket privilege; other modes can require it. |
| `ss` | Socket inspection | Numeric UIDs are compatibility projections, not native owner identities. |
| `dig` | Query a chosen DNS server | Direct queries do not change resolvd configuration. |
| `nc` | TCP/UDP communication | OpenBSD implementation with Debian portability patches; optional TLS mode is not built. |
| `tcpdump` | Live capture or saved-capture decoding | Live packet access needs native authority; ordinary file read access suffices for saved captures. |
| `arping` | Local-link ARP probes | Uses packet authority and does not trace routed paths. |
| `nmap` | Targeted host/service inspection | Connect mode and raw-packet modes have different authority requirements. |

Ordinary echo does not use a POSIX group-range setting to authorize callers.
PNP still evaluates its traffic. Raw and packet sockets require enabled
`SeTcbPrivilege`; a tool's behavior-selection flag cannot confer it. MTR can
fall back to echo datagrams when raw sockets are unavailable.

Nmap selects probing behavior using native privilege rather than projected
UID zero. `-sT -Pn` requests TCP connect probing without raw host discovery;
`--privileged` and `NMAP_PRIVILEGED` only select behavior. Its scripts retain
the caller's authority. User data lookup uses an absolute `$HOME/.nmap` with
normal FACS checks. Ncat and Nping are not included by this recipe.

tcpdump rejects Unix `-Z` identity dropping because a numeric UID change does
not reduce native authority. Launch it with the intended native token.
Capture filters select observations, not allowed traffic, and a captured
frame can still be rejected elsewhere in the stack.

Named libpcap savefiles and Nmap logs are created with protected owner-only
native descriptors. Existing destinations must be regular, singly linked,
owned by the effective principal, and provably protected for that owner.
Rotation follows the same creation rule. Streams supplied by a caller,
stdout, shell redirection, and script-owned file operations instead follow
their own destination policy. A private file does not protect its directory
entry from a principal authorized to replace it.

## Transfer and relay

curl uses OpenSSL's system trust paths. Cookie, HSTS, and Alt-Svc saved state
receives a private descriptor for the effective principal at creation, with
no fallback to Unix mode bits. Equal projected UIDs do not confer access.
State output requires a regular writable destination; ordinary downloads
use normal destination policy. `wcurl` uses curl for file downloads.

socat supports TCP, UDP, Unix sockets, files, PTYs, process execution, and
OpenSSL TLS. It starts only explicitly requested listeners or children, under
the caller's token. Unix ownership, mode, umask, identity-switch, chroot, and
network-namespace options are rejected rather than presented as native
isolation. TUN, POSIX message queues, readline, and libwrap are excluded.
Regular relay output uses ordinary FACS policy. Select the expected TLS
identity and anchors for a private service explicitly.

For synchronized contents and private cryptographic output, use
[Copying Contents and Checking TLS](~peios/compatibility/transfers-and-tls).

## Registration and throughput

`whois` follows registration-server queries and referrals under normal PNP
rules. Its recipe excludes `mkpasswd` and IDN conversion: supply ASCII or
already converted punycode. `/etc/whois.conf` can override server selection.

For a measurement between cooperating hosts, start `iperf3 -s` on the
receiver and `iperf3 -c HOST` on the sender. UDP, reverse direction, and
parallel streams use `-u`, `-R`, and `-P`. The default port is 5201; the
server
needs native bind authority and policy for control and test traffic.
Installation starts no measurement service.

iperf3 uses anonymous in-memory payload buffers. Received `-F` output and PID
files use protected owner-only creation and validate existing regular,
singly linked destinations before truncation. Send-side inputs use ordinary
read checks; logs and redirected output use their destination's policy.
Optional RSA authentication restricts measurement access but neither creates
a Peios logon nor encrypts measured traffic. Protect private keys and the
server's authorized-user file separately.
