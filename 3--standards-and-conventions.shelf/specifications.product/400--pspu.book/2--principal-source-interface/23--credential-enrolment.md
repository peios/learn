---
title: Credential Enrolment
description: EnrollCredential — relaying a principal's addition or removal of one of their own credentials to the source that holds it, the capability that gates it, and the proof the source must take first.
---

A PGSS Logon enrolment (PGSS §2.23) reaches the source that holds the
principal as a conversation of its own kind. It opens with
`EnrollCredential`, runs the relayed interrogation of §2.12, and ends in
`CredentialChanged` or `Refusal`.

```
  authority                              source
    |------------ EnrollCredential ---------->|   conversation N
    |<----------- CredentialRequest ----------|   the current credential
    |------------ CredentialResponse -------->|
    |<------ CredentialChanged | Refusal -----|
```

It is the sibling of the credential change (§2.21), and every rule that
section states binds here unless this section says otherwise: routing to
the source authoritative for the principal, `AuthorityUnavailable` while
a configured source is absent, the principal as established fact, the
terminals out of place, and `Abandon`.

## EnrollCredential

`msg_type` = `0x0008`. Authority to source. **Opens a conversation.**

| Field | Encoding | Limit |
|---|---|---|
| `start` | nested `CredentialEnrollStart`, length-framed | PGSS §2.23 |
| `principal` | length-framed bytes (SID) | 68 bytes |

`start` is the client's `CredentialEnrollStart`, nested whole for the
reason `ChangeCredential` nests its start (§2.21). `principal` is the
user of the client's token, established by the authority from the
client's socket, exactly as in `ChangeCredential`. A source MUST NOT add
a credential to, or remove one from, any other principal in this
conversation.

## The capability

An authority MUST NOT send `EnrollCredential` to a source that did not
declare `ENROLLS_CREDENTIALS` (§2.8). Where the source that holds the
principal did not declare it, the authority MUST answer the client
`PermissionDenied`: for that principal it does not offer enrolment, and
PGSS §2.23 gives that answer to an authority that does not.

`ENROLLS_CREDENTIALS` and `CHANGES_CREDENTIALS` are independent. A
source may change passwords and not enrol keys, or the reverse.

## The interrogation

The source MUST establish that the principal can present a credential
they already have, other than the one being enrolled, before it adds or
removes anything, for `Add` and `Remove` alike, and MUST refuse with
`AuthenticationFailed` where they cannot. The token the authority read
`principal` from is not that proof. A source that cannot ask for such a
credential for this principal — the principal has none, or signs in only
with the kind being enrolled — MUST refuse with `AccountRestricted`
before asking anything.

The source decides which credential types it enrols and what material it
accepts. It SHOULD check the material before asking for proof, MUST
check it again when it applies the change, and MUST refuse material it
will not accept with `CredentialRejected`. A source MUST NOT send
`CredentialRejected` in any conversation but this one, and an authority
receiving it in any other MUST end the client's conversation with
`Internal` (§2.13).

## CredentialChanged

The successful terminal is `CredentialChanged` (§2.21), sent only once
the change is durable: an added key is one the source's next
`Authenticate` will accept where the principal's policy allows keys, and
a removed key is one it will not.

A source that declares `PUSHES_CHANGES` MUST send `Changed` (§2.17)
before `CredentialChanged`, as for any other change to what it holds.

Enrolment does not change which credentials the principal may sign in
with; that remains the source's administration.
