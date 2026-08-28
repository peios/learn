---
title: IPC on Peios
type: concept
description: Every Linux IPC mechanism, with two answers each — does it carry the sender's identity, and what protects the object — and the rules that fall out of them.
related:
  - peios/linux-compatibility/peer-credentials
  - peios/linux-compatibility/system-v-ipc
  - peios/impersonation/peer-tokens
  - peios/access-decisions/overview
---

Peios does not add IPC primitives: Linux's are the substrate. What it adds is a consistent answer, for each of them, to two questions that Linux mostly leaves to convention — **whose identity, if any, does a message carry**, and **what decides who may use the object**. This page is the map. The rule of thumb it boils down to: identity travels only where one kernel sees both ends and the channel can carry an attested token; everything else is protected as an object, with a security descriptor, and conveys no identity at all.

## Identity flows over Unix sockets, and nowhere else

`AF_UNIX` is where identity lives. Every connection end has a **conveyed-identity register**: initialised when the connection is made — the accepted end sees the client, the connecting end sees the listener — and advanced by tokens attached in-band as the reader's position passes them. `KACS_SO_PEER_TOKEN` reads the register; `KACS_SCM_TOKEN` attaches a token to a send, gated exactly as impersonation would be; `KACS_SO_PASS_TOKEN` automates that on the sender's side; `KACS_SO_IMPERSONATION_LEVEL` bounds what the other end may do with what it receives. Stream and seqpacket sockets carry the register; datagram sockets carry identity per message only; a `socketpair()` starts with an empty register until one side conveys something. [Peer tokens](~peios/impersonation/peer-tokens) covers the programming model and [Peer credentials](~peios/linux-compatibility/peer-credentials) the migration from `SO_PEERCRED`.

That is the whole list. In particular:

- **TCP and UDP, loopback included** carry no kernel-attested identity: the kernel attests only what it saw both ends of, and the other end of a network socket is a claim. Cross-machine identity is authd's job, and the token it produces re-enters through the ordinary install path.
- **Netlink** needs nothing: kernel-bound requests run synchronously in the sender's context, and the capability checks on both the socket's opener and the sender go through the capability switchboard, so they are already token decisions (Peios Kernel TRM §3.10.4).
- **`AF_VSOCK`** spans two kernels; process identity across it is a claim, not an attestation.
- **Pipes and FIFOs** carry no identity, structurally: there is no ancillary channel, and with several writers there is no "whose bytes". Linux has none either, so nothing is lost — but note the trap below.
- **System V and POSIX queues** deliver bytes and a type. `SI_MESGQ` and `ucred`-style crumbs carry projected values and are informational.
- **Signals** name a sender by projected `si_pid`/`si_uid`; the decision to deliver was made on the token (Peios Kernel TRM §3.7), the crumb is not evidence.

## Everything is an object with a descriptor

Where no identity flows, a descriptor decides who may use the thing, exactly as for a file:

| Mechanism | What protects it |
|---|---|
| Socket file | The directory's descriptor for `bind`, the socket file's for `connect` (write-class right) |
| Abstract socket | A descriptor stamped at `bind`, checked on `connect` and datagram send |
| Pipe | Descriptor possession, nothing else |
| FIFO | The file's descriptor at open; the directory's for creation |
| System V queue, segment, semaphore array | A descriptor stamped at creation, addressed by kind and id ([System V IPC](~peios/linux-compatibility/system-v-ipc)) |
| POSIX shm, named semaphore, message queue | They are files — tmpfs under `/dev/shm`, mqueuefs inodes — with file descriptors |
| memfd, eventfd, pidfd, io_uring ring | Descriptor possession; pidfd operations are process-access checks |
| Shared mappings | Rights consumed from the descriptor at `mmap`; see the note on revocation below |
| Watches (`inotify`, `fanotify`) | The watched object's read-class right (Peios Kernel TRM §3.9.4) |

Descriptor passing (`SCM_RIGHTS`) is untouched: it moves descriptors, and a token descriptor riding it is *delegation* — the receiver gets a handle — as distinct from `KACS_SCM_TOKEN`, which is *attestation* of who sent the bytes.

## Three rules that fall out

**A FIFO is not a named pipe.** NT programs use named pipes for identity-carrying request/response with impersonation. The Linux object with that name — a FIFO — carries no identity and cannot; porting that pattern means an `AF_UNIX` socket with `KACS_SO_PEER_TOKEN`, never a FIFO.

**A name you did not create is not evidence.** Abstract socket names, System V keys, and entries under `/dev/shm` and `/dev/mqueue` are claim-on-create: whoever gets there first owns the object, and the descriptor then protects the object — not the name. Peios-native services bind filesystem paths in directories they own and clients authenticate the *peer*, not the name; anyone using a first-come namespace creates with an exclusive flag and treats failure as a signal, not a retry.

**Revocation does not reach established mappings.** Editing a descriptor narrows future opens; it cannot take pages back from a process that has already mapped them. If that matters, replace the file instead of editing it, or end the process. The general form of this rule — decisions are made when a handle is created — is in [Access decisions](~peios/access-decisions/overview).

## Where to go next

For the socket options and the register in detail, read [Peer tokens](~peios/impersonation/peer-tokens).

For how System V objects get and expose their descriptors, read [System V IPC](~peios/linux-compatibility/system-v-ipc).
