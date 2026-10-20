---
title: Abandon
description: Telling a source a conversation will not continue, and why the protocol would leak state without it.
---

`msg_type` = `0x0004`. Authority to source. No fields beyond the header.

Tells a source that a conversation will not continue: the client hung
up, a limit was reached, or the authority terminated the logon for
reasons of its own.

## Why it exists

Without it, a client that disconnects mid-prompt leaves the source
holding conversation state forever. A source cannot detect this for
itself — it is not party to the client's connection — so the authority
has to say.

## Rules

1. An authority MUST send `Abandon` for any conversation it opened that
   will not reach a terminal state, unless the connection itself is
   being torn down.
2. A source MUST discard all state for the conversation on receipt, and
   MUST NOT reply.
3. `Abandon` is not a terminal message *from* the source, and no
   `Assertion` or `Refusal` follows it. If one arrives anyway, the
   authority MUST ignore it — the conversation is gone, and a late
   answer to an abandoned question is at best stale.
4. A source that receives `Abandon` for a conversation it does not know
   MUST ignore it. It has already cleaned up, which is the outcome the
   message wanted.

> [!NOTE]
> The natural implementation is to send `Abandon` from whatever owns the
> conversation's lifetime, on any path that does not reach a terminal
> state — including error paths. An authority that sends it only on the
> tidy path will leak conversations exactly when things are already
> going wrong.
