---
title: "destination.*"
description: "Every field the evman catalogue defines under destination: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `destination`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="destination.address"></a>`destination.address`

- **Type:** `str.ip`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The address the traffic was going to, rendered in the textual form for its
family.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="destination.attribution"></a>`destination.attribution`

- **Type:** `str.enum`
- **Values:** `socket-stamp` · `no-kacs-state` · `unstamped` · `no-namespace` · `loopback-sender-lost` · `time-wait` · `stack-handled` · `no-sending-socket` · `multicast-or-broadcast` · `no-receiver` · `principal-unreadable`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Why the destination endpoint was given the attribution it has. **Not
emitted today**: NTFE decides it on every flow and encodes it nowhere, so
`destination.endpoint` and `destination.unattributed` are all a record
carries. The values are those of `source.attribution`;
`multicast-or-broadcast` and `no-receiver` are the inbound paths that give
`shared` and `none`.

**Carried by:**

No event carries this field yet.

## <a id="destination.endpoint"></a>`destination.endpoint`

- **Type:** `str.enum`
- **Values:** `program` · `kernel` · `shared` · `none`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

What stands at the destination end of the traffic, when that end is on this
machine. `program` is a process's socket, and the `destination.socket.*`
fields then say whose. `kernel` is the network stack itself. `shared` is
inbound multicast or broadcast, delivered to every socket bound to the
port and so attributable to none of them. `none` means nothing on the
machine will receive the traffic: a port nobody is listening on, which is
the signature of a port scan. Present only on flow-layer records, and absent
when the destination is a remote machine.

**Carried by:**

No event carries this field yet.

## <a id="destination.file.parent.inode"></a>`destination.file.parent.inode`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The inode number of the directory a rename moves an object into. Subject
to the same caveats as `object.file.inode`.

**Carried by:**

No event carries this field yet.

## <a id="destination.file.path"></a>`destination.file.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The path an object went to, in an operation on two objects such as a
rename or a link. Where it came from is `source.file.path`.

**Carried by:**

No event carries this field yet.

## <a id="destination.mac"></a>`destination.mac`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The link-layer address the traffic was going to, written as six
colon-separated lowercase hexadecimal octets. Known only from a frame's
Ethernet header, so it is absent for outbound traffic judged at the IP
seats, where the frame has not been built yet, even when `source.mac` is
present.

**Carried by:**

No event carries this field yet.

## <a id="destination.port"></a>`destination.port`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The transport port the traffic was going to. Present only for protocols
that have ports.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="destination.socket.process.guid"></a>`destination.socket.process.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The durable GUID of the process recorded on the destination endpoint's
socket when it was stamped. Unlike the process ID it is never reused, so it
still names the right process after that process has exited.

**Carried by:**

No event carries this field yet.

## <a id="destination.socket.process.name"></a>`destination.socket.process.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The short name of the process recorded on the destination endpoint's
socket when it was stamped. It is the kernel's command name, at most 15
characters and lossily sanitised, so two different programs can share it;
it is a hint for a person, not an identity.

**Carried by:**

No event carries this field yet.

## <a id="destination.socket.process.pid"></a>`destination.socket.process.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The process ID recorded on the destination endpoint's socket when it was
stamped. A socket can outlive the process that created it, so this process
may have exited and its ID been reused; `destination.socket.process.guid`
is the identity that survives that.

**Carried by:**

No event carries this field yet.

## <a id="destination.socket.token.service-sid"></a>`destination.socket.token.service-sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The per-service SID of the token stamped on the destination endpoint's
socket, when that token belongs to a service. It is found among the token's
enabled groups and is always the 32-byte S-1-5-80 form. Absent for a socket
that no service stands behind.

**Carried by:**

No event carries this field yet.

## <a id="destination.socket.token.sid"></a>`destination.socket.token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The user SID of the token KACS stamped on the destination endpoint's
socket. It is the identity the socket was stamped with, not necessarily the
identity of whoever reads from it now. Present only when
`destination.endpoint` is `program`.

**Carried by:**

No event carries this field yet.

## <a id="destination.stratum.flags"></a>`destination.stratum.flags`

- **Type:** `uint.flags`
- **Values:** `0x1 create` · `0x2 read-only` · `0x4 absent-may`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The configuration flags of the stratum an object was written into, as the
mount option set them. Decoded as `source.stratum.flags` is. A copy-up
always writes into the stratum flagged `create`, so on a copy-up record
this field says nothing new; it matters where an object was written in
place.

**Carried by:**

No event carries this field yet.

## <a id="destination.stratum.index"></a>`destination.stratum.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

Which stratum an object was written into, by index within the mount's stack.

**Carried by:**

- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)

## <a id="destination.stratum.path"></a>`destination.stratum.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The filesystem path of the stratum an object was written into.

**Carried by:**

- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)

## <a id="destination.token.guid"></a>`destination.token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of a token the operation created, which did not exist
before it: the result of a duplicate, a filter or a token creation.

**Carried by:**

No event carries this field yet.

## <a id="destination.unattributed"></a>`destination.unattributed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Whether NTFE confessed that it could not attribute the destination endpoint
to a principal. When true, every rule condition on that endpoint's identity
was false for this traffic rather than evaluated. **False does not prove
the endpoint was attributed**: a `program` endpoint whose token could not
be read still reads false here.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman`, `ntfe.evman`, `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
