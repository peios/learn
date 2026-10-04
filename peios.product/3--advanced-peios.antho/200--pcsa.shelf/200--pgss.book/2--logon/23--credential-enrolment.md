---
title: Credential Enrolment
description: How a principal adds a credential of their own, such as an SSH public key, or removes one — the opening message, why it names nobody, the proof of the current credential it requires, and the denial that says the material was refused.
---

A principal adds a credential of their own beside the ones they have, or
removes one, by opening a conversation on `/run/logon.sock` with
`CredentialEnrollStart`. The only credential this section defines for
enrolment is an SSH public key (§2.D). The authority asks for the
principal's current credential, in the rounds of §2.8, and ends the
conversation with `CredentialChanged` or `AccessDenied` (§2.10).

```
client                                   authority
  |                                          |
  |-------- CredentialEnrollStart ---------->|   principal = the peer
  |                                          |   material: the key, or which
  |<--------- CredentialRequest -------------|   the current credential
  |---------- CredentialResponse ----------->|
  |                                          |
  |<-- CredentialChanged --------------------|   terminal
  |         or AccessDenied                  |
```

It is the sibling of a credential change (§2.20), and everything that
section says about the shape of the conversation, whose credential is
affected, and the terminal holds here unless this section says
otherwise. The difference is where the material travels: a change
collects the new credential in a round, while an enrolment carries it in
the opening message. That is possible because the material is public: an
SSH public key, or the fingerprint of one.

## CredentialEnrollStart

`msg_type` = `0x0031`. Client to authority. Opens the conversation; MUST
be the first message.

| Field | Encoding | Limit |
|---|---|---|
| `supported_credential_types` | length-framed bytes, one `u8` per type | 32 |
| `action` | `u8` | §2.B |
| `credential_type` | `u8` | §2.B |
| `material` | string | 16384 |

Every field is mandatory. The message is newer than the rule that lets a
trailing field be absent, so there is no older client whose silence
needs a default, and a truncated message read with one could perform an
action nobody asked for. An authority MUST refuse a
`CredentialEnrollStart` that ends before `material` with
`MalformedRequest`.

### supported_credential_types

The credential types the client can render, for the proof the authority
will ask for. It carries the meaning and the capability rule of the §2.7
field of the same name, and a decoder MUST drop a value it does not
recognise rather than refuse the message.

### action

`1`, `Add`: enrol `material` as a new credential of the principal. `2`,
`Remove`: remove the credential `material` identifies. The values are
instructions rather than statements of capability, so a decoder MUST
refuse one it does not recognise with `MalformedRequest`.

### credential_type

The kind of credential being added or removed, from the credential types
of §2.B. Only `SshPublicKey` is defined for enrolment. An authority MUST
refuse any other with `PermissionDenied`.

### material

For `Add` of an `SshPublicKey`, one line of an OpenSSH public key file,
such as `~/.ssh/id_ed25519.pub`: the key type, the base64 key and an
optional comment. The comment MAY become the key's label.

For `Remove` of an `SshPublicKey`, the key's fingerprint as
`ssh-keygen -l` writes it: `SHA256:` and the unpadded base64 of the
SHA-256 of the key blob (§2.D).

## Whose credential

The principal whose credentials change is the **user of the connected
peer's token**, as in §2.20, and for the same reason: a field naming a
principal would let anything that reaches the socket ask to add a key to
anybody's account. The message carries no identifier, and an authority
MUST NOT enrol a credential for, or remove one from, any other principal
in this conversation.

An authority MUST refuse, with `AccountRestricted`, a principal for
whom it holds no credential it can ask for as proof (below). That
includes a service identity (§2.19), a platform identity no source
holds, a principal that authenticates with no credential at all, and a
principal that authenticates only with the kind of credential being
enrolled. The `reason` SHOULD tell the principal that an administrator
can make the change for them.

## Proof of the current credential

**Both actions require it.** An authority MUST establish, within the
conversation, that the principal can present their current credential
before it adds or removes anything, and MUST refuse with
`AuthenticationFailed` where they cannot. The rule and its wording
requirement are §2.20's.

A token shows that someone signed in, not that the person at the
keyboard now is that person. A key added from an unattended terminal is
a way back into the account for whoever added it, and outlives every
session; a key removed from one locks its owner out of every machine
that trusts it. Neither can be undone by signing in again.

The proof is a credential the principal already has and that is not the
one being enrolled. A principal who signs in only with SSH keys cannot
prove themselves with a key over this socket, since there is no
transport to bind the proof to (§2.D); such a principal is refused as
above.

## Checking the material

The authority decides what it accepts: which key types and sizes, how
many keys a principal may hold, and whether a key may be held twice. It
SHOULD check the material before it asks for the current credential, so
that a principal is not asked for a password to be told their key is
unreadable, and it MUST check it again when it applies the change, since
the principal's credentials may have changed between the two.

An authority MUST refuse material it will not accept with
`CredentialRejected`, and SHOULD say why in `reason`: unreadable, an
unsupported type, a key the principal already has, one more than the
principal may have, or, for `Remove`, no key of the principal's with
that fingerprint. `CredentialRejected` answers only this message (§2.B).
It MUST NOT be used where the proof failed: that is
`AuthenticationFailed`, and the two are separate so that a client can
tell "your key" from "your password".

Enrolment does not change which credentials a principal may sign in
with. Whether an enrolled key is accepted at sign-in is the authority's
policy for that principal, as it is for a key an administrator adds.

## CredentialChanged

The successful terminal message is §2.20's `CredentialChanged`, with
every rule that section states for it: no fields and no descriptor, and
not sent until the change is the one a subsequent logon will be tested
against. For `Remove`, that means the key no longer authenticates the
principal at their next sign-in.

Sessions already established are left as they were. Removing a key does
not end a session that was signed in with it; ending one is §2.22's.

## Access to the socket

The socket admits the peers §2.20 admits, for the same reason, and §2.20's
rules on deciding who may originate a logon and on keeping such peers
off the originators' bound on conversations apply unchanged.

## An authority that does not offer it

An authority MAY decline to offer enrolment, or to offer it for some
principals. One that declines MUST refuse `CredentialEnrollStart` with
`PermissionDenied`, and is conforming.
