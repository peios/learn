---
title: Credential Change
description: ChangeCredential and CredentialChanged — relaying a principal's change of their own credential to the source that holds it, and why the principal is never a claim.
---

A PGSS Logon credential change (PGSS §2.20) reaches the source that
holds the principal as a conversation of its own kind. It opens with
`ChangeCredential`, runs the relayed interrogation of §2.12, and ends in
`CredentialChanged` or `Refusal`.

```
  authority                              source
    |------------ ChangeCredential ---------->|   conversation N
    |<----------- CredentialRequest ----------|   the current credential
    |------------ CredentialResponse -------->|
    |<----------- CredentialRequest ----------|   the new one
    |------------ CredentialResponse -------->|
    |<------ CredentialChanged | Refusal -----|
```

It is not an `Authenticate` that ends differently. A change asserts
nobody, so it carries nothing an authority could mint from, and keeping
the two apart by message type keeps the path that mints unreachable from
this one (§2.4).

## ChangeCredential

`msg_type` = `0x0007`. Authority to source. **Opens a conversation.**

| Field | Encoding | Limit |
|---|---|---|
| `start` | nested `CredentialChangeStart`, length-framed | PGSS §2.20 |
| `principal` | length-framed bytes (SID) | 68 bytes |

### start

The client's `CredentialChangeStart`, nested whole (§2.7), for the
reason `Authenticate` nests `LogonStart` (§2.11): it grows on PGSS
Logon's schedule, and a field appended there must not displace
`principal`. Its `supported_credential_types` binds what may be prompted
for, exactly as in a logon.

### principal

The principal whose credential changes: the user of the client's token,
established by the authority from the client's connected socket and
never from a message body.

It names both who asked and who is being changed, because PGSS Logon
gives a client no way to name anybody else. A source MUST treat it as
established fact, MUST NOT change the credential of any other principal
in this conversation, and MUST NOT take a principal from anything the
client supplies in it.

### Routing

An authority MUST send `ChangeCredential` only to the source
authoritative for `principal`'s domain (§2.18), and MUST NOT offer the
change to any other source. The rule and its reason are those of §2.11:
a credential offered to the wrong source is a credential handed to it.

Where no registered source is authoritative for `principal` and a
configured source is absent, the authority MUST answer the client
`AuthorityUnavailable` rather than refusing the account. The absent
source may be the one that holds it, and "this account has nothing to
change" would turn an outage into a statement about the account.

An authority MUST NOT send `ChangeCredential` to a source that did not
declare `CHANGES_CREDENTIALS` (§2.8).

## The interrogation

The rounds are those of §2.12, unchanged: `CredentialRequest` and
`CredentialResponse` carrying PGSS Logon's bodies, relayed and policed
by the authority as they are in a logon. The source decides what to ask
for.

A source MUST establish that the principal can present their current
credential before changing it (PGSS §2.20), and MUST refuse with
`AuthenticationFailed` where they cannot. The token the authority read
`principal` from is not that proof.

A source that proves the current credential in one round and collects
the new one in a later round MUST NOT change the credential if the
current credential has itself changed in between. Otherwise an
administrator's reset between the two rounds would be overwritten on the
strength of the credential it replaced.

## CredentialChanged

`msg_type` = `0x8008`. Source to authority. **The only successful
outcome of a change conversation.** No fields.

A source MUST NOT send it until the new credential is the one it will
verify at its next `Authenticate` for this principal — until the change
is durable. The authority relays it to the client as PGSS Logon's
`CredentialChanged`, and PGSS §2.20 forbids reporting a change that a
subsequent logon would not see.

## Refusal

A change that does not end in `CredentialChanged` ends in `Refusal`
(§2.13). A source MUST refuse:

- with `AccountRestricted`, a principal it holds no changeable
  credential for: one that authenticates with no credential, one
  designated only for service logons, or one that is disabled;
- with `AuthenticationFailed`, a current credential that does not
  verify;
- with `ConversationLimit`, a change it gives up on for want of an
  acceptable new credential.

## Terminals out of place

An authority MUST treat an `Assertion` in a change conversation, and a
`CredentialChanged` in any other conversation, as a source fault. It
MUST end the client's conversation with `Internal`, MUST NOT mint from
the assertion, and MUST NOT report the change.

`Abandon` (§2.14) applies unchanged. A source discards everything it
held for the conversation, including what a completed round established.
