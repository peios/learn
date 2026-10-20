---
title: Porting Identity and IPC
type: how-to
description: Replace Linux identity assumptions with Peios token and object contracts when porting services.
---

Review authority decisions separately from compatibility display. Peios
exposes
Linux UIDs, GIDs, mode bits, and capability interfaces so programs can
operate,
but those values do not describe the full security token or descriptor.

## Replace credential assumptions

Do not authorize a request solely because `geteuid()` or `SO_PEERCRED` reports
zero. A numeric projection omits claims, groups, privileges, restrictions,
impersonation level, and process trust. Cosmetic credentials can also differ
from the token. Name-service lookup helps display identities; it does not
create or authenticate them.

Do not treat successful `setuid()` as a privilege drop. Without the relevant
Peios privilege it is a silent no-op; the privileged identity-swap path is
unimplemented and fails. Setuid-bit exec has different cosmetic behavior.
Use a correctly scoped service token or the supported token API, and verify
the effective identity. The [setuid
reference](~kernel/internals/kacs/linux-credentials/setuid-behaviour)
also covers `setfsuid`, `access`, exec, and the absence of a general `uid0`
helper.

The kernel neutralizes conflicting Linux DAC decisions through its
[capability switchboard](~kernel/internals/kacs/linux-credentials/dac-neutralisation).
Some capabilities are allowed for compatibility, some map to Peios privileges,
and some are denied. The displayed capability mask is not an independent
source of authority. Removing Linux capabilities or assigning file capability
xattrs is not a substitute for controlling Peios token privileges.

Filesystem-facing projected identity also matters to quotas, remote servers,
and stacking filesystems. Preserve that distinction when diagnosing a local
success followed by a remote refusal. Peios does not make a remote server
understand a local descriptor automatically.

## Choose a channel with the required identity

| Channel | Identity and authority boundary |
|---|---|
| Unix stream or seqpacket socket | Native peer-token transport can bind local identity to the connection and conveyed requests. |
| Unix datagram | Identity is conveyed per message; do not use a connection register as its substitute. |
| TCP, UDP, or VSOCK | No local kernel attestation of the remote principal, including loopback IP traffic. Use an explicit authentication protocol. |
| Pipe or FIFO | Bytes and descriptor/file authority; no per-request token identity. |
| System V or POSIX queue | Object permissions protect use; payload and projected notification identity do not authenticate a principal. |
| Shared memory | Mapping and handle permissions; no identity attached to each memory write. |
| Netlink | Kernel-bound operations use the kernel's sender/opener checks; this is not a generic peer-token channel. |

A FIFO cannot replace an identity-carrying request/response named-pipe API.
Use a Unix socket with the native token protocol. `SCM_RIGHTS` delegates a
handle; token attestation is a different contract. Bind a received request to
its received token before concurrent work changes the socket's latest peer
state. The [SDK token guide](~peios/sdk-access-control/working-with-tokens)
and [socket identity reference](~kernel/internals/kacs/network-objects/socket-identity)
define capture, impersonation, and transport limits.

## Protect objects and their names

System V objects carry descriptors, and mode changes do not replace those
descriptors. Their numeric keys, abstract socket names, and shared-memory
names remain claim-on-create namespaces. Create exclusively where appropriate
and treat a pre-existing name as a condition to investigate, not proof of the
expected server. Prefer service-owned directories and authenticate the peer.

The [System V reference](~kernel/internals/kacs/system-v-ipc/objects-and-their-descriptors)
defines creation policy and descriptor operations by object kind and ID.
A restricted caller is not categorically refused every object created by its
parent: the complete descriptor and restricting identity determine the result.

Existing descriptors and mappings can retain authority after a policy change.
Replacing a name or tightening a descriptor does not remove another process's
old mapping. Design revocation and shutdown explicitly rather than promising
that a permissions edit retracts already-delivered data.

## Keep diagnostic provenance

Linux process accounting remains a compatibility facility, gated through its
capability-to-privilege mapping. Native KMES/eventd records carry Peios
identity
and process correlation, subject to each producer's schema and delivery
limits. Do not promise that every Linux accounting field has a native event
counterpart. Audit metadata and signal sender crumbs are observations, not
credentials to reuse for authorization.
