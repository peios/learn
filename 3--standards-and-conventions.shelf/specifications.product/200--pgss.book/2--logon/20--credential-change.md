---
title: Credential Change
description: How a principal changes their own credential — the opening message, why it names nobody, the proof it requires, and a terminal that mints nothing.
---

A principal changes their own credential by opening a conversation on
`/run/logon.sock` with `CredentialChangeStart`. The authority asks for
what it requires, in the rounds of §2.8, and ends the conversation with
`CredentialChanged` or `AccessDenied` (§2.10).

```
client                                   authority
  |                                          |
  |-------- CredentialChangeStart ---------->|   principal = the peer
  |                                          |
  |<--------- CredentialRequest -------------|   the current credential
  |---------- CredentialResponse ----------->|
  |                                          |
  |<--------- CredentialRequest -------------|   the new one
  |---------- CredentialResponse ----------->|
  |                                          |
  |<-- CredentialChanged --------------------|   terminal
  |         or AccessDenied                  |
```

Adding a credential beside the ones a principal has, such as an SSH
public key, or removing one, is the sibling conversation of §2.23.

Everything §2.3 says about the shape of a conversation applies
unchanged: one conversation per connection, bounded rounds, exactly one
terminal message. The client stays generic here as it does in a logon.
It renders the prompts it is given and returns the answers, and it does
not know what is being changed or how.

## CredentialChangeStart

`msg_type` = `0x0030`. Client to authority. Opens the conversation; MUST
be the first message.

| Field | Encoding | Limit |
|---|---|---|
| `supported_credential_types` | length-framed bytes, one `u8` per type | 32 |

`supported_credential_types` carries the meaning and the capability rule
of the §2.7 field of the same name. It binds the authority, and a
decoder MUST drop a value it does not recognise rather than refuse the
message.

Unlike the §2.7 field, it is not optional. This message is newer than
the rule that made that field optional, so there is no older client
whose silence needs a default. An authority MUST refuse a
`CredentialChangeStart` that ends before the field with
`MalformedRequest`.

## Whose credential

The principal whose credential changes is the **user of the connected
peer's token**, established from the socket as §2.4 requires. The
message carries no identifier, and an authority MUST NOT change the
credential of any other principal in this conversation.

The absence of an identifier is deliberate. A field naming a principal
would let anything that can reach the socket ask to change anybody's
credential, with only knowledge of that credential in the way. That is a
guessing surface over every account the authority holds, open to every
principal the socket admits. Taking the principal from the token
confines each caller to their own account.

An authority MUST refuse, with `AccountRestricted`, a change for a
principal it holds no changeable credential for. That includes a service
identity (§2.19), a platform identity no source holds, and a principal
that authenticates with no credential at all.

## Proof of the current credential

A token is not proof enough. An authority MUST establish, within the
conversation, that the principal can present their current credential
before it changes that credential, and MUST refuse with
`AuthenticationFailed` where they cannot.

A token shows that someone signed in. It does not show that the person
at the keyboard now is that person. An unattended terminal holds a token
too, and a credential changed from one cannot be recovered by signing in
again, because the credential needed to sign in is the one that changed.

`AuthenticationFailed` keeps the wording rule of §2.10 here: `reason`
MUST NOT say what was wrong with the credential. The caller cannot use
the distinction to learn about another account, since only their own is
reachable, but a reason that varied would still tell a guesser which
part of a guess was right.

## The new credential

What the authority asks for, and what it accepts, is its own policy. An
authority that refuses a proposed credential MAY say why in a message of
`Error` severity (§2.8) and ask again, within its round limit. An
authority that gives up MUST end the conversation with
`ConversationLimit`.

The new credential is credential material like any other. It is
collected and handled under §2.12, and the client neither knows nor
cares that it is new.

## CredentialChanged

`msg_type` = `0x8030`. Authority to client. The successful terminal
message; nothing follows it.

It has no fields and no ancillary data. A change mints no token and
creates no session: the caller already holds a session, and the change
leaves it as it was. A client MUST NOT expect a descriptor with this
message, and MUST close one if one arrives.

An authority MUST NOT send `CredentialChanged` until the new credential
is the one a subsequent logon will be tested against. A principal told
about a change that is not yet durable can lose it, and finds out only
when the old credential works and the new one does not.

What a change does to sessions already established is the authority's
policy. This chapter specifies none.

## Access to the socket

Every principal permitted to change their own credential needs connect
access to `/run/logon.sock` (§2.5), and most of them may not originate a
logon. The socket's descriptor therefore admits both kinds of peer and
cannot tell them apart. An authority whose descriptor admits a peer that
may not originate logons MUST decide, from each peer's identity (§2.4),
whether that peer may originate one. It MUST NOT treat reaching the
socket as that permission.

The two kinds of peer SHOULD NOT share one bound on concurrent
conversations (§2.5). A principal who can reach the socket to change a
password can also open connections and hold them open, and a shared
bound they could exhaust would stop the console signing anyone in.

## An authority that does not offer it

An authority MAY decline to offer credential change. One that declines
MUST refuse `CredentialChangeStart` with `PermissionDenied`, and is
conforming.
