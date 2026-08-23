---
title: Running udd
type: how-to
description: Creating a domain with udd new, running the daemon, the data directory and ephemeral mode, the GIP fabric and the two-DC harness, and what to do when udd refuses to start.
related:
  - universal-directory/getting-started/what-is-universal-directory
  - universal-directory/the-console/the-debug-console
  - universal-directory/concepts/persistence
  - universal-directory/reference/json-api
---

**`udd`** is the Universal Directory server daemon. It lives in the `ud` repository as the first crate of a Cargo workspace.

Creating a domain and running one are **separate commands**, deliberately. `udd` on its own never creates anything: a mistyped `--data-dir`, an unattached mount, or a half-finished restore must fail loudly rather than silently birth an empty directory that answers queries as if it were yours.

## Create a domain

```
cd ud
cargo run -- new
```

```
udd: created a domain in ud-data
udd:   machine object /Domain Controllers/dc1
udd:   networkAddress 10.0.0.5
udd:   networkAddress dc1
udd: run it with `udd --data-dir ud-data`
```

`udd new` creates the [data directory](~universal-directory/concepts/persistence)'s footprint, materialises the domain, mints this machine's identity keypair, plants this machine's object in the tree, and exits. It refuses a directory that is not empty — whatever is in there, moving it aside is your call, not the daemon's.

| Option | Effect |
|---|---|
| `--data-dir <path>` | Where to create the domain. Default `./ud-data`. |
| `--name <name>` | The machine object's name. Default: this machine's hostname, or `DC1` if that is unusable. |
| `--gip-port <port>` | Advertise this port in the machine's addresses instead of leaving the [well-known GIP port](~universal-directory/reference/base-schema) implicit. |
| `--address <endpoint>` | Advertise this address instead of detecting any. Repeatable. |

### The machine object and its key

The machine object is an ordinary `computer` object under `/Domain Controllers`, carrying the [`machine` facet](~universal-directory/reference/base-schema): its detected addresses and its public key (`machineKey`). Nothing about it is privileged — rename it, move it, edit its addresses in the console. Its placement is convention only; nothing in UD looks for domain controllers by path.

The **private** half of the keypair never enters the directory. It lives in the data directory's write-once `machine-key` file, beside the domain's generation files, and the whole data directory is created owner-only (mode 0700) because it holds a private key and the entire directory database. The key is this machine's GIP identity.

### Check the detected addresses

Address detection is a best effort, and you should check it. `udd` asks the kernel which local address it would use to reach the wider network — one per IP family, by opening a UDP socket and reading back its source address, sending no packets — and adds the hostname if it is a legal DNS name.

Behind NAT, inside a container, or on a multi-homed machine, that answer can be confidently wrong. This is why every value is printed at creation, overridable with `--address`, and editable afterwards like any other attribute.

## Run it

```
cargo run                      # or: cargo run -- --data-dir /srv/ud
```

```
udd: storage [ud-data] recovered: generation 2, 53 objects, 14 frames replayed
udd: debug console listening on http://127.0.0.1:5389
```

`udd` recovers the domain from the files and serves it. It never creates. Pointing it at a directory that holds no domain is an error that tells you to run `udd new`.

| Option | Effect |
|---|---|
| `--data-dir <path>` | The directory holding the domain. |
| `--ephemeral` | No disk at all. The identical [persistence](~universal-directory/concepts/persistence) code path runs against an in-memory filesystem, with a fresh domain created at startup and everything vanishing at exit. |
| `--listen <addr>` | The debug console and API address. Default `127.0.0.1:5389`. |
| `--gip-bind <addr>` | The GIP fabric's UDP bind. Default `0.0.0.0:5390`; ephemeral daemons default to a free loopback port. |

`--ephemeral` is the one mode that creates implicitly, because a RAM directory has nothing to recover by definition.

The server serves everything from one listener: **`/`** is the [debug console](~universal-directory/the-console/the-debug-console), a browser UI embedded in the binary, and **`/api/…`** is the [JSON API](~universal-directory/reference/json-api). The address is currently a hardcoded constant — `127.0.0.1:5389`, a mnemonic nod to LDAP's port 389 — and becomes configurable when `udd` grows more configuration.

GIP link connections are **encryption-only**: no trust rides them, so an open fabric port exposes nothing but a QUIC handshake. Trust lives one layer up. Every service conversation is a **channel**, end-to-end encrypted and mutually authenticated against the directory's keys, and the daemon admits only IK-authenticated channels naming a registered service from a machine whose key the directory holds.

## The fabric

A running daemon **discovers every other machine in the directory** — any alive `computer` object carrying a `machineKey` and a `networkAddress`, placement irrelevant — and holds a supervised QUIC connection to each: dialled on discovery, kept alive with keepalives, and redialled with exponential backoff when it dies.

Every dialled link is **identified** the moment it connects. The daemon opens a `gip/ident` channel over it: a payload-free conversation whose Noise handshake *is* the content, proving to the dialer that the far end holds the key the directory binds to that machine, and proving to the acceptor who dialled. A link whose ident fails — the machine at that address is not who the directory claims — is closed on the spot.

Identification is also what lets two daemons that have both dialled each other keep **exactly one connection**. The lower machine GUID's dial survives; the other side gracefully retires its own and holds the peer's connection instead. The console shows this as *via inbound*, the same state a NAT-ed peer's partner lives in permanently.

Watch all of it live in the console's **fabric** tab: peer states, RTT, byte counters, identified inbound connections named by machine, and an event stream narrating every dial, ident, tiebreak, loss, and retry.

### ud/msgs

The first real service riding the fabric is **`ud/msgs`** — machine-to-machine talk, sendable from the console's [msgs tab](~universal-directory/the-console/the-debug-console) or with `POST /api/msgs/send`.

It is deliberately *talk, not email*: online-only, no queueing, no storage. Its real job is to prove the fabric end to end. Every message is one short-lived authenticated channel over the held connection, and every send reports an honest fate — *delivered* with the round trip, *failed* when provably undelivered, or *unconfirmed* when the channel died between the send and the ack.

Try it in the two-DC harness: send both ways, then kill one daemon and watch the outcomes tell the truth.

## The two-DC dev harness

`dev/two-dc.sh` stands up a complete two-machine domain on localhost. It runs **`udd dev-fixture`**, which builds two data directories sharing one domain *out-of-band*: machine A creates the domain and performs the admission write for machine B — exactly the shape `udd join` will later perform over the wire — and B receives everything through the real pull machinery in-process. The script then launches both daemons on separate ports and prints their console URLs and PIDs.

Open both fabric tabs, kill one daemon, and watch the other back off and recover in real time.

## When udd refuses to start

A report of `N torn bytes truncated` after a crash is **normal**. It is unacknowledged residue of writes that were still in flight; nothing that was ever confirmed is affected.

A refusal to start is different. Recovery will not guess around damage, so `udd` stops and names the file and offset. Three cases have specific causes:

- **The files are damaged.** Restore the directory from a copy, or move it aside and create a new domain.
- **The `machine-key` file is missing, damaged, or belongs to a different node.** A file copied from another machine's data directory must never let one machine wear another's identity. Restore the file from a backup of the same data directory, or move the directory aside and create the domain again.
- **The directory holds a node but no domain.** A `udd new` was interrupted before the domain's birth was durable. The birth is a single all-or-nothing frame, so there is no half-built directory to salvage: move the directory aside and create it again.

A boot **warning** that the directory's machine object does not carry this machine's key means someone edited or deleted the object. That one is fixable in the console.

## What to know before you start

- **There is no authentication.** Anyone who can reach the port has full control of the directory. The listener binds to loopback only. Treat `udd` as a local development tool.
- **The fabric does not carry directory data yet.** Daemons hold real QUIC link connections and real services ride them, but replication between daemons arrives with the DRS-over-GIP work. The [replication engine](~universal-directory/concepts/replication) itself still syncs only between in-process nodes.
- **One process per data directory.** Nothing locks the directory yet; two daemons on the same files would interleave destructively.

## What a fresh directory contains

`udd new` materialises the root object, `/Configuration`, `/Configuration/Schema`, `/LostAndFound`, and `/Domain Controllers`, with the complete [base schema](~universal-directory/reference/base-schema) — 48 definition objects, all flagged system and immutable — plus the one machine object for the machine you ran it on.

Everything else is yours to create, and survives restarts.
