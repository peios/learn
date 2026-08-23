---
title: The Conversation
description: A logon is a conversation rather than a call — who may speak when, how it is bounded, and how it ends.
---

A logon is a conversation, not a call. The client opens it, the
authority asks for whatever the principal's policy requires, and the
authority ends it.

```
client                                   authority
  |                                          |
  |------------- LogonStart ---------------->|
  |                                          |
  |<--------- CredentialRequest -------------|   round 1
  |---------- CredentialResponse ----------->|
  |                                          |
  |<--------- CredentialRequest -------------|   round 2 (if required)
  |---------- CredentialResponse ----------->|
  |                                          |
  |<-- AccessGranted (+ token fd) -----------|   terminal
  |         or AccessDenied                  |
```

## Why a conversation

The value of this shape is that **the client stays generic**. It does
not know what a password is. It renders the prompts it is given,
collects the answers, and returns them.

That is what makes multi-factor authentication,
password-expiry-forces-change, smartcards, or a policy that asks for a
second factor only from an unfamiliar host, changes to *authorities*
rather than to every client on the system. A protocol that named its
credential kinds would have to be revised, and every client rebuilt, for
each one.

Most logons are one round: the authority asks for everything the
principal's policy requires, in one array, and decides. The
conversational shape exists for what one round cannot express — choosing
between authentication paths, or a shared account where one credential
unlocks a requirement for another.

## Sequence rules

A conversation MUST proceed as follows.

1. The client sends exactly one `LogonStart`. It MUST be the first
   message. An authority MUST reject any conversation that opens with
   something else.
2. The authority sends zero or more `CredentialRequest` messages. Each
   MUST be answered by exactly one `CredentialResponse` before the
   authority sends anything further.
3. The authority sends exactly one terminal message, `AccessGranted` or
   `AccessDenied`.
4. Both parties close the connection.

The authority MAY send a terminal message at any point after
`LogonStart`, including before any `CredentialRequest`. Zero rounds is a
conforming conversation: an authority that can decide from `LogonStart`
alone — a pre-authenticated caller, or a refusal on logon type — is not
required to ask for anything.

A client MUST NOT send a `CredentialResponse` that was not solicited by
a `CredentialRequest`. An authority MUST reject one that was not.

## Bounding the conversation

An authority MUST bound the number of rounds it will conduct and MUST
bound the time it will wait for a `CredentialResponse`. Neither bound is
fixed by this chapter, since both are policy. An authority that exhausts
either MUST terminate with `AccessDenied` carrying `ConversationLimit`
rather than closing silently, so that the client can distinguish a
policy limit from a crash.

## Termination

Exactly one terminal message is sent. After it, the authority MUST NOT
send anything further on that connection, and MUST close it.

A connection that closes without a terminal message is an *abnormal*
termination. A client MUST treat it as a failed logon and MUST NOT retry
automatically, since the reason is unknown and may be a policy refusal
the authority could not express.
