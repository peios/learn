---
title: The identity facts
description: The third rung — who stands at each local end of a flow, read once from the socket KACS stamped, fixed for the flow's life, and judged as the Flow layer's Local and Remote facts.
---

The identity facts (rung 3 on PEI-598) answer the question the address
facts cannot: not *where* a flow goes but *who* on this machine is
speaking or listening. They are Flow-layer facts by the same law as
`Related` and `Start.*` — a flow has one answer for its whole life — and
they are the first facts PNP reads from somewhere other than the packet.
KACS provides them; the engine resolves them once per flow.

## What KACS stamps on a socket

Every inet socket carries a **governing identity**, recorded by KACS in
the socket's security state (§3.12.2): the caller's *effective* token —
so a service thread impersonating a client attributes the socket to the
client, as audit does — and the process facts of that moment: the
process GUID, the thread-group id and the task's `comm`. The stamp is
taken at every act that commits the socket to a role: creation, `bind`,
`listen`, `connect`, inheritance at `accept`, and `KACS_SO_RESTAMP`. The
last stamp governs, which is how a listener handed to another program
(socket activation, descriptor passing) is governed as that program's.
A kernel socket is stamped as the kernel's, with no token.

The engine reads the stamp through one accessor,
`pkm_kacs_socket_owner()` (`<linux/peios_pnp.h>`), which hands it a
counted reference to the token and a copy of the process facts. The
facts outlive the process; the reference outlives the socket.

## What stands at an end

`identity.c` classifies each local end of a flow by **whether anyone
answers**, not by whether a socket structure exists. The result is the
`Local` fact (`program`, `kernel`, `shared`, `none`) and, for a program,
the principal behind `Local.*`.

**Outbound**, at `LOCAL_OUT`: the sending socket's stamp. A stamped
program socket is `program`; a kernel socket, or no socket at all
(resets, ICMP errors, IGMP) is `kernel`.

**Inbound**, at `LOCAL_IN`, a transport lookup for the receiver of this
very packet:

- UDP to a multicast or broadcast destination is `shared` before any
  lookup: the stack delivers it to every socket bound to the port — one
  flow, many endpoints — and the per-program question belongs to the
  *join*, not to the packet. `Local.*` is absent.
- TCP, UDP and UDP-Lite are looked up by tuple, the way the netfilter
  socket match does — listeners included, and through the same hash a
  `SO_REUSEPORT` group steers by, so the sentence names the socket that
  will actually receive. Early demux may already have found it. Any
  other protocol is looked up among raw sockets bound to it.
- A socket found is `program` (a request minisock stands for its
  listener; a `TIME_WAIT` minisock is nobody's: `kernel`).
- Nothing found: `kernel` if the stack has a handler registered for the
  protocol — ICMP and ICMPv6 (neighbour discovery, router advertisements,
  MLD), IGMP, the tunnel and IPsec outers that are decapsulated and
  re-enter the ingress seat as their inner packet — else `none`, which
  the stack will answer with a reset or an unreachable.

The classification is a rule, not a list of protocols. Two consequences
are documented rather than special-cased: SCTP, a socket transport whose
table lives inside its module, reads `kernel` while the module is
loaded; and a ping socket's echo reply pairs with the outbound request in
conntrack and inherits the outbound `program` sentence, so the direct
lookup is deferred.

The lookup runs **once per flow**, on the first judgment, and only when
a `Flow` forest is published: a permissive machine pays nothing.

## Loopback: both ends

A loopback flow has two local ends and two sentences (§6.8). The
outbound seat resolves both on the first packet — its own end from the
socket, the other by running the receiver lookup early on the
loopback-destined packet — and records them on the flow's extension.
The inbound seat's judgment, on the same packet, reads both from there:
`Local.*` is its own end and `Remote.*` the sender's. The inbound seat
cannot see a loopback packet's sender itself (loopback transmission
orphans the buffer), so a flow whose extension could not be allocated
reads `Remote` as absent there, confessed. Off loopback `Remote` is
always absent: nothing is provable about a peer yet.

## Fixed for the flow's life

The identities are recorded on the conntrack extension at the first
judgment, per slot, beside the direction and the interface, and never
replaced: a re-judgment after a policy change or a time edge sees the
same principal, and a later restamp of the socket, a fork after
`accept`, or a `SO_REUSEPORT` sibling taking over the port changes
nothing for flows already judged. The extension holds one counted token
reference per slot and releases it when conntrack frees the flow. Two
CPUs racing on a new flow's first packets may both resolve; the first
record stands, as the first sentence does, and the loser releases its
reference.

## Across the bridge

The flow view carries, per end, the kind, the process facts and a
borrowed token pointer. The bridge (`kacs/pnp_runtime.rs`) implements
pnp-core's `Principal` trait over the token — user SID, enabled-group
membership (deny-only groups are invisible to policy), integrity level,
confinement SID and capabilities, the per-service SID found among the
enabled groups, the process GUID as text — without copying the group
list: a token may carry a thousand groups and the judgment runs in
softirq context, so the snapshot borrows a view and asks membership
questions of it. The view is lock-free: group SIDs are fixed at token
creation and each group's attributes are an atomic.

Nothing about a SID's meaning lives in the kernel. `Local.Service.Equal
= resolvd` is turned into the service's SID at ingestion by pnp-core,
with the same derivation peinit and authd use to mint it (the SHA-1 of
the uppercased UTF-16LE name under `S-1-5-80`); `Local.User.Equal =
LocalService` by a table of well-known names. The viewer resolves the
other way, from the service definitions in the registry.

## What the stream says

A `Flow` event and a flow record carry both ends: the kind, the process
GUID, pid and comm, the user SID and the service SID (ABI 4, §6.A,
§6.B). An end that could not be attributed — a socket with no KACS
state, an inet socket nobody stamped, a loopback sender the inbound
seat could not see — is confessed: `identity_unresolved` in the status,
`PEIOS_PNP_EV_F_IDENTITY_UNRESOLVED` on the event, and the flag on the
flow record's slot.

## At rest: the listeners dump

The same stamp, read without a packet: `PEIOS_PNP_IOC_LISTENERS`
(`listeners.c`) walks the listening TCP hash and the bound UDP and
UDP-Lite tables of the root namespace the way `/proc/net/tcp` and
`/proc/net/udp` do — each bucket under its lock, records copied out
between buckets — and reports every socket prepared to receive with the
identity that governs it. It is the attack surface as a list, by whom,
and it exercises the stamp before a single flow is judged.

## What was decided against

- **Identity in the per-packet layers.** A packet carries no owner; the
  socket does. `Local.*` in a `Packet` rule is linted as never present,
  and `Present` on it refuses the generation.
- **Many sentences for a shared receiver.** Inbound multicast is one
  flow with many endpoints; modelling N judgments would have made the
  join-time question a per-packet one. `shared` and a later gate on
  `IP_ADD_MEMBERSHIP` (C11) instead.
- **Copying the group list into the snapshot.** Up to 1024 SIDs per
  token, in softirq: the `Principal` view answers membership instead.
- **`Program.Trust` and the image hash.** PIP is under review, and
  unsigned binaries are not hashed at exec today; both wait.
