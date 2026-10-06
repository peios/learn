---
title: "source.*"
description: "Every field the evman catalogue defines under source: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `source`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="source.address"></a>`source.address`

- **Type:** `str.ip`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The address the traffic came from, rendered in the textual form for its
family.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="source.attribution"></a>`source.attribution`

- **Type:** `str.enum`
- **Values:** `socket-stamp` · `no-kacs-state` · `unstamped` · `no-namespace` · `loopback-sender-lost` · `time-wait` · `stack-handled` · `no-sending-socket` · `multicast-or-broadcast` · `no-receiver` · `principal-unreadable`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Why the source endpoint was given the attribution it has. **Not emitted
today**: NTFE decides it on every flow and encodes it nowhere, so
`source.endpoint` and `source.unattributed` are all a record carries. The
values name the paths the attribution can take: `socket-stamp` is the
principal KACS stamped on the socket; `no-kacs-state`, `unstamped` and
`no-namespace` fell back to the kernel because no stamp could be read;
`loopback-sender-lost` is the sender of a loopback flow that the inbound
seat cannot see; `time-wait`, `stack-handled` and `no-sending-socket` are
the stack answering for itself; `principal-unreadable` is a program
endpoint whose token could not be read.

**Carried by:**

No event carries this field yet.

## <a id="source.endpoint"></a>`source.endpoint`

- **Type:** `str.enum`
- **Values:** `program` · `kernel` · `shared` · `none`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

What stands at the source end of the traffic, when that end is on this
machine. `program` is a process's socket, and the `source.socket.*` fields
then say whose. `kernel` is the network stack itself: a reset, an ICMP
error, a protocol the stack consumes, or a socket nobody could attribute.
`shared` and `none` arise only at a receiving end, as `destination.endpoint`
describes. Present only on flow-layer records, and absent when the source is a remote
machine. Read `source.unattributed` before taking `kernel` at its word.

**Carried by:**

No event carries this field yet.

## <a id="source.file.path"></a>`source.file.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The path an object came from, in an operation on two objects such as a
rename or a link. The object is at `destination.file.path` afterwards.
Neither is the record's `object.file.path`: the operation acted on both.

**Carried by:**

No event carries this field yet.

## <a id="source.mac"></a>`source.mac`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The link-layer address the traffic came from, written as six colon-separated
lowercase hexadecimal octets. Known only where an Ethernet header exists:
from the frame at the device seats, and, for outbound traffic at the IP
seats, the sending device's own address. Absent on a device with no
Ethernet header.

**Carried by:**

No event carries this field yet.

## <a id="source.port"></a>`source.port`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The transport port the traffic came from. Present only for protocols that
have ports.

**Carried by:**

- [`ntfe.verdict.reported`](~peios/events/ntfe/ntfe-verdict-reported)

## <a id="source.rsi.generation"></a>`source.rsi.generation`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The restart generation of a registry source slot: how many times the slot
has been resumed by a re-registering source after going down. Zero for a
source that has never been restarted. A count that climbs quickly is a
source crash-looping.

**Carried by:**

No event carries this field yet.

## <a id="source.rsi.generation-validated"></a>`source.rsi.generation-validated`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The source restart generation that a cached key handle was last validated
against. A handle whose validated generation is behind
`source.rsi.generation` has outlived a source restart and must be
revalidated before use, because the key it names may no longer exist.

**Carried by:**

No event carries this field yet.

## <a id="source.rsi.hive"></a>`source.rsi.hive`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The hive the offending source data belonged to, where the failure could be
attributed to one. Absent when the data was malformed before a hive could
be determined.

**Carried by:**

- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)

## <a id="source.rsi.in-flight"></a>`source.rsi.in-flight`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The number of requests dispatched to a registry source and still awaiting
a reply, at the moment of the record. Bounded by the configured concurrency
ceiling per source, so a value at that ceiling means new requests are
queuing behind slow ones.

**Carried by:**

No event carries this field yet.

## <a id="source.rsi.queued"></a>`source.rsi.queued`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

The number of requests queued for a registry source and not yet delivered
to it, at the moment of the record. Distinct from `source.rsi.in-flight`:
a queued request has not reached the source at all, so it is discarded
rather than failed if the source goes down.

**Carried by:**

No event carries this field yet.

## <a id="source.rsi.slot"></a>`source.rsi.slot`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `lcs.evman`

Which registry source slot supplied the data, by index. Sources are the
userspace backends that serve registry content to the kernel, so this names
the backend rather than anything about the caller.

**Carried by:**

- [`lcs.source.response.rejected`](~peios/events/lcs/lcs-source-response-rejected)

## <a id="source.socket.process.guid"></a>`source.socket.process.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The durable GUID of the process recorded on the source endpoint's socket
when it was stamped. Unlike the process ID it is never reused, so it still
names the right process after that process has exited.

**Carried by:**

No event carries this field yet.

## <a id="source.socket.process.name"></a>`source.socket.process.name`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The short name of the process recorded on the source endpoint's socket when
it was stamped. It is the kernel's command name, at most 15 characters and
lossily sanitised, so two different programs can share it; it is a hint for
a person, not an identity.

**Carried by:**

No event carries this field yet.

## <a id="source.socket.process.pid"></a>`source.socket.process.pid`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The process ID recorded on the source endpoint's socket when it was
stamped. A socket can outlive the process that created it, so this process
may have exited and its ID been reused; `source.socket.process.guid` is the
identity that survives that.

**Carried by:**

No event carries this field yet.

## <a id="source.socket.token.service-sid"></a>`source.socket.token.service-sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The per-service SID of the token stamped on the source endpoint's socket,
when that token belongs to a service. It is found among the token's enabled
groups and is always the 32-byte S-1-5-80 form. Absent for a socket that no
service stands behind.

**Carried by:**

No event carries this field yet.

## <a id="source.socket.token.sid"></a>`source.socket.token.sid`

- **Type:** `bin.sid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The user SID of the token KACS stamped on the source endpoint's socket. It
is the identity the socket was stamped with, not necessarily the identity
of whoever writes to it now. Present only when `source.endpoint` is
`program`.

**Carried by:**

No event carries this field yet.

## <a id="source.stratum-previous.index"></a>`source.stratum-previous.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The position, within the mount's stack, of the stratum that provided an
object before the change the record describes. Present exactly when
`source.stratum-previous.path` is.

**Carried by:**

No event carries this field yet.

## <a id="source.stratum-previous.path"></a>`source.stratum-previous.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The filesystem path of the stratum that provided an object before the
change the record describes. Read with `source.stratum.path`: a record
where the two differ is an object that now comes from a different layer,
so a reader of the merged path sees different contents without the path
having changed.

**Carried by:**

No event carries this field yet.

## <a id="source.stratum.flags"></a>`source.stratum.flags`

- **Type:** `uint.flags`
- **Values:** `0x1 create` · `0x2 read-only` · `0x4 absent-may`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The configuration flags of the stratum an object was read from, as the
mount option set them: `+create`, `+ro` and `+am`. `create` marks the one
stratum new objects and copy-ups are written into, `read-only` forbids
writing into the stratum in place, and `absent-may` lets the mount succeed
while the stratum's directory does not exist.

**Carried by:**

No event carries this field yet.

## <a id="source.stratum.index"></a>`source.stratum.index`

- **Type:** `uint`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

Which stratum an object was read from, by index within the mount's stack.
Absent when no provider was determined, as `source.stratum.path` is.

**Carried by:**

- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)
- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="source.stratum.path"></a>`source.stratum.path`

- **Type:** `str.path`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `stratafs.evman`

The filesystem path of the stratum an object was read from. Absent when
the refusal was raised before any provider was determined — creation,
tmpfile, and the heads of link and rename — in which case
`source.stratum.index` is absent too, and the two agree that no provider
was involved.

**Carried by:**

- [`stratafs.file.copied-up`](~peios/events/stratafs/stratafs-file-copied-up)
- [`stratafs.mutation.refused`](~peios/events/stratafs/stratafs-mutation-refused)

## <a id="source.token.guid"></a>`source.token.guid`

- **Type:** `bin.guid`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kernel.evman`

The durable GUID of the token an operation derived a new one from, by
duplicating or filtering it. The new token is `destination.token.guid`.

**Carried by:**

No event carries this field yet.

## <a id="source.unattributed"></a>`source.unattributed`

- **Type:** `bool`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

Whether NTFE confessed that it could not attribute the source endpoint to a
principal. When true, every rule condition on that endpoint's identity was
false for this traffic rather than evaluated. **False does not prove the
endpoint was attributed**: a `program` endpoint whose token could not be
read still reads false here, and its identity conditions failed just the
same.

**Carried by:**

No event carries this field yet.

*Generated from `kernel.evman`, `lcs.evman`, `ntfe.evman`, `stratafs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
