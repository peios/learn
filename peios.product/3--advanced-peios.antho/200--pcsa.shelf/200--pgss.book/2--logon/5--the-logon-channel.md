---
title: The Logon Channel
description: /run/logon.sock — the normative path, its access control, one conversation per connection, and why the channel does not multiplex.
---

## Socket

An authority MUST listen on a `SOCK_STREAM` Unix domain socket at:

```
/run/logon.sock
```

The path is normative. It is the standard's path, not an
implementation's, and a client MUST NOT require configuration to find
it.

## Access control

The socket MUST carry a security descriptor granting connect access to
the principals permitted to originate logons. See §2.4 for why this, and
not process integrity, is the control.

## One conversation per connection

A connection carries exactly one conversation. The connection **is** the
conversation's identity.

There is therefore no correlation identifier in the header, and none is
needed: a message belongs to the conversation it arrived on. This
removes a class of error and attack — a forged or confused identifier
cannot attach a credential response to somebody else's logon, because
there is no identifier to forge.

It also bounds the credential's lifetime by the connection's, which
makes that the kernel's job to enforce rather than the authority's to
remember.

An authority MUST close the connection after sending its terminal
message. A client MUST close after receiving one.

> [!NOTE]
> A protocol whose connections are long-lived and shared reaches the
> opposite conclusion, and multiplexes. PSI does (PSPU §2.7), and so
> does this chapter's own identity channel (§2.14). The difference is not
> inconsistency: a logon client's connection exists for one logon and
> is discarded, so paying for multiplexing here would buy nothing and a
> correlation identifier would only add something to forge.

## Concurrency

An authority MUST serve conversations concurrently. A logon that stalls
— a principal who walks away mid-prompt — MUST NOT prevent other logons
from proceeding.

An authority MUST bound the number of conversations it will serve at
once, and MUST bound the time a conversation may remain open. Both are
policy; neither is fixed here.

## Descriptor passing

The channel MUST support ancillary data (`SCM_RIGHTS`). The token is
transferred as a file descriptor alongside `AccessGranted` — see §2.9.
