---
title: Network diagnostic tools
type: guide
description: Work from a connectivity, DNS, listener or TLS symptom to the next check, then choose an Experimental diagnostic tool within Peios access and file-security restrictions.
related:
  - peios/networking/the-net-command
  - peios/networking/name-resolution
  - peios/networking/network-policy
  - peios/networking/rsync-and-openssl
---

Start with the symptom below. Run read-only checks before changing profiles,
firewall rules or service state, and keep the output that explains the
failure. The tools retain your native identity and access restrictions;
installing a tool does not grant network or capture privileges.

## Start with the symptom

| Symptom | Check | What to do with the result |
|---|---|---|
| No connectivity | `net status` | Find the affected interface's carrier, verdict, profile and readiness. `IGNORE` or `DOWN` is a profile-rule question; no carrier is a link question. |
| Carrier, but no DHCP address | `net status`, then `net profiles` and `net rules` | Check `Address.Offered`, `Address.Families` and the selected rule. An unanswered-discovery warning can mean no server or blocked DHCP traffic. |
| Only a `169.254…` address | `net status` | This is link-local fallback, not a routed lease. DHCP discovery continues. Check server reachability and the baseline DHCP rules. |
| Address present, no gateway | `net status` | Check `Route.Offered` or your pinned `Route.Gateway`. An unreachable pinned gateway is logged as a failed route addition. |
| IP connection works, names fail | `resolv status`, `resolv query <name>` | Check servers, domains, netd connection, and `notfound` versus `unavailable`; use [DNS troubleshooting](~peios/networking/name-resolution#not-found-versus-unavailable). |
| One TCP service fails | `ss -lnt` on the receiving machine; `nc -vz 192.0.2.1 443` from the caller | Confirm the listener and intended address/port, then check native port authority and PNP. Replace the example address and port. |
| Settings were written but behavior did not change | `net status`; as administrator, `net policy wait` and `net policy` | Check interface and firewall acceptance separately. A refused generation leaves the previous one active. |
| TLS certificate errors | [Strict OpenSSL check](~peios/networking/rsync-and-openssl#tls-diagnostics-and-network-policy) | Check both trust and the expected peer identity. SNI alone is not hostname verification. |

For daemon errors, use the service logs:

```sh
evctl 'LOGS FROM netd SINCE 1h ago TAKE 40'
evctl 'LOGS FROM resolvd SINCE 1h ago TAKE 40'
```

If a profile or rule is wrong, follow [the safe change checklist](~peios/networking/configuring-profiles#before-you-change-anything)
and verify it afterwards. Restarting netd can remove offered addresses and
routes while it acquires them again; it is not the first connectivity test.
The [netd failure modes](~peios/advanced-peios/netd/failure-modes/failure-modes)
and [resolvd failure modes](~peios/advanced-peios/resolvd/failure-modes/names-do-not-resolve)
give the detailed failure paths.

## Choose a tool

Experimental includes these tools alongside `net`, `resolv` and `trust`:

| Command | Purpose | Example |
|---|---|---|
| `rsync` | Synchronize file contents locally or over SSH | `rsync -rlt source/ destination/` |
| `openssl` | Inspect TLS, certificates and cryptographic material | `openssl x509 -in certificate.pem -noout -text` |
| `curl` | Transfer data using URLs | `curl https://example.org/` |
| `wcurl` | Download files using curl | `wcurl https://example.org/file.txt` |
| `ping` | Check ICMP echo replies and round-trip time | `ping -c 3 192.0.2.1` |
| `tracepath` | Investigate a route and its path MTU | `tracepath 192.0.2.1` |
| `dig` | Send DNS queries to a chosen DNS server | `dig @127.0.0.53 example.org A` |
| `ss` | Inspect sockets | `ss -lnt` |
| `nc` | Send or receive TCP and UDP streams | `nc -vz 192.0.2.1 443` |
| `whois` | Query domain and IP address registration records | `whois example.org` |
| `iperf3` | Measure TCP or UDP throughput between cooperating hosts | `iperf3 -c 192.0.2.1` |
| `socat` | Relay data between sockets, files, terminals and programs | `socat - TCP:192.0.2.1:443` |
| `tcpdump` | Capture packets or decode saved captures using libpcap | `tcpdump -nr capture.pcap` |
| `mtr` | Repeatedly probe a route and report latency and loss | `mtr -r -c 10 192.0.2.1` |
| `traceroute` | Probe each hop towards a destination | `traceroute -n 192.0.2.1` |
| `arping` | Send ARP probes on a local IPv4 link | `arping -I eth0 -c 3 192.0.2.1` |
| `nmap` | Discover hosts and inspect listening services | `nmap -sT -Pn -n -p 443 192.0.2.1` |

These are command examples, not an instruction to scan or capture an unrelated network. Test hosts and traffic you are authorized to inspect. The documentation addresses above are examples; replace them with the host you want to test. `net` remains the interface to netd for network configuration and status. The iproute2 package supplies `ss`; it does not add `ip` or `tc` as alternative configuration tools.

## Echo and network policy

Ordinary IPv4 and IPv6 echo datagram sockets are available to every principal. `ping` needs neither a privileged executable nor a raw socket for its ordinary echo operation. Peios does not use Linux's POSIX group-range setting to decide who may open these echo sockets.

PNP still evaluates the resulting packets. Rules can block requests and replies, inbound or outbound, including loopback traffic. A missing reply can mean filtering, routing trouble or a host that does not answer echo; it does not by itself prove that the host is down. Ordinary echo never receives the bypass reserved for refusal packets generated by PNP itself.

Raw sockets remain subject to the existing kernel authority checks. Options that require raw sockets can therefore fail for an ordinary caller. The package grants no raw-packet privilege and does not change the caller's token.

## Routes, capture and scanning

Ordinary UDP `traceroute` and echo-datagram probes do not require raw-socket authority. MTR uses the ordinary echo-datagram fallback when raw sockets are unavailable. Other probe modes can require enabled `SeTcbPrivilege`, the existing Peios authority for raw and packet sockets. This applies to live tcpdump capture, ARP probes and Nmap's raw scanning modes. `arping` is part of iputils and operates on the local IPv4 link; it does not trace routed paths.

Nmap selects its default probing behaviour from the caller's enabled native privilege, rather than its projected Unix UID. Use `-sT -Pn` for ordinary TCP connect scans that skip raw host discovery. `--privileged` and `NMAP_PRIVILEGED` only select behaviour; they grant no authority. Nmap includes its NSE scripts and data, but this package does not install Ncat or Nping. NSE scripts run with the invoking principal's access. User data lookup uses an absolute `$HOME/.nmap`, with normal FACS checks.

All these tools retain the invoking token. There are no set-ID helpers, file capabilities, automatic privilege grants or new PNP exceptions. tcpdump's Unix `-Z` privilege-drop option is rejected because changing a projected UID does not reduce native authority. Launch capture with the intended native authority from the outset. Probe traffic remains subject to PNP; a capture filter only selects what is recorded and is not a firewall rule. Seeing a packet in a capture does not prove that a later policy check allowed delivery.

Named libpcap savefiles, including tcpdump `-w` output, and Nmap's named scan logs are created with an atomic, protected owner-only FACS descriptor. An existing output must be a regular file with one hard link, owned by the effective principal and protected by an owner-only descriptor. Shared destinations, symlinks and special files are refused before truncation or append. Capture rotation creates each new file under the same rule. Choose a directory you control: private file contents do not stop another principal with directory authority from replacing entries.

Reading captures requires ordinary FACS read access, without raw-socket privilege. Output to `-`, shell redirection, caller-supplied libpcap streams and NSE scripts' own file operations follow the destination's existing policy. They are not converted into private named logs by these patches.

## Socket and terminal relays

socat supports TCP, UDP, Unix sockets, files, PTYs, program execution and OpenSSL TLS. It starts listeners or programs only when explicitly requested. They retain the caller's native identity, port authority and PNP restrictions. Unix ownership, mode, umask, identity-switch, chroot and network-namespace address options are rejected during option parsing; those options cannot establish native isolation. Configure FACS and native launch authority separately.

Regular relay files use the destination's normal FACS policy. Place sensitive output in a private directory. TLS uses OpenSSL trust handling; supply the intended peer name and trust anchors when using an explicit private service. TUN, POSIX message queues, readline and libwrap support are not included in this build.

## DNS and socket inspection

`resolv` asks resolvd about Peios name resolution. `dig` sends a DNS query directly, which is useful for inspecting the local stub or comparing an explicitly named server. Use `@127.0.0.53` to query resolvd's local stub. Direct DNS requests still traverse PNP and do not change the system's DNS configuration.

`ss` reports the socket information the kernel exposes to the caller. Any numeric Unix UID shown is a compatibility projection, not a Peios SID or proof of the effective principal. Use PNP's identity information when investigating native ownership or policy decisions.

## Transfers and saved state

curl uses OpenSSL's system trust paths, maintained by trustd. Its cookie jar, HSTS cache and Alt-Svc cache are created atomically with a protected FACS descriptor belonging to the effective principal. A second principal does not gain access merely because it has the same projected Unix UID. Failure to create that descriptor does not fall back to Unix mode bits.

Normal downloaded documents use the destination's usual FACS policy. Shared writable directories can still allow another principal to remove or replace directory entries; save sensitive state in a directory you control. curl's saved-state files must be regular writable file destinations rather than special devices.

`nc` is the OpenBSD implementation with Debian's portability patches. This package does not supply its optional TLS mode. It listens only when explicitly invoked in a listening mode; installing it starts no service. Listeners and connections remain subject to native port reservations and PNP.

## Registration queries and throughput

`whois` queries remote registration servers. The package includes the query client, without the separate `mkpasswd` program. Domain names must be ASCII or already converted to their punycode form; this build does not include an IDN conversion library. The optional `/etc/whois.conf` compatibility file can override server selection. Queries and any referrals remain subject to PNP.

Start `iperf3 -s` on the receiving host, then run `iperf3 -c HOST` on the sending host. Add `-u` for UDP, `-R` to reverse the data direction, or `-P 2` for two parallel streams. The default server port is 5201. The invoking principal must have the necessary port authority, and PNP must allow both the control connection and the test traffic. Installing the package starts no service and grants no port reservation, privilege or policy exception.

iperf3 uses anonymous in-memory files for its stream buffers. Received `-F` files and PID files are created with a protected, owner-only FACS descriptor for the effective principal. An existing destination must be a regular file with one hard link, owned by that principal and already protected by an owner-only descriptor; shared files, symlinks and special files are refused before truncation. Send-side `-F` files and authentication inputs use ordinary FACS access checks. Log files and redirected output follow their destination's usual policy, so choose a private directory when results are sensitive.

Optional RSA authentication restricts who may run a measurement against that server; it does not create a Peios logon or encrypt the measured traffic. Authentication debug output omits decoded credentials. Protect the server's private key and authorized-user file with FACS and use a directory you control for saved state.
