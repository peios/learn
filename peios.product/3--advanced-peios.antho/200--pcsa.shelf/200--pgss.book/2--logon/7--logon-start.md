---
title: LogonStart
description: The client's opening message — logon type, identifier, tty and remote host, and the credential types it can collect.
---

`msg_type` = `0x0001`. Client to authority. Opens the conversation; MUST
be the first message.

## Layout

| Field | Encoding | Limit |
|---|---|---|
| `logon_type` | `u8` | §2.B |
| `identifier_type` | `u8` | §2.B |
| `identifier` | length-framed bytes | 1024 |
| `tty` | string | 128 |
| `remote_host` | string | 256 |
| `supported_credential_types` | length-framed bytes, one `u8` per type | 32 |

Everything here is *asserted by the client*, and §2.4 governs all of it.

## logon_type

The kind of session the client is asking for. **A proposal**, which the
authority MUST constrain against the verified peer — see §2.4.

Values are defined by KACS and listed for reference in §2.B.

## identifier_type and identifier

Together these name the principal. `identifier_type` says how to read
`identifier`; `identifier` is **opaque bytes**, not a string.

Bytes rather than a string because an identifier is not always text. A
certificate thumbprint, a smartcard serial, or a binary principal name
are all reasonable identifiers, and a protocol that insisted on UTF-8
would exclude them. An authority that expects text MUST validate the
encoding itself.

An identifier MAY be empty. An empty identifier means *the principal is
not named here* — the authority is expected to determine it from the
credential, as with a smartcard that carries its own identity.

`identifier_type` is distinct from `credential_type` (§2.8): this is the
claim of identity, that is the proof. A passkey names a principal and
proves them in one artefact; a username names them and proves nothing.

## tty and remote_host

Unverified context, both optional, both empty when absent.

`tty` names the terminal the logon is happening on, where there is one.
`remote_host` names where a network logon came from.

An authority MAY use either in policy and MAY record either in its audit
trail. It MUST NOT treat either as established. A client that lies about
them is not prevented from doing so.

## supported_credential_types

Every credential type this client can render, one byte each.

This is the client declaring its capabilities, and it is **binding on
the authority**: an authority MUST NOT send a prompt for a credential
type absent from this list (§2.8).

A client that supports nothing sends an empty list. That is meaningful
rather than degenerate — it says "I can complete a logon that requires
no interaction, and nothing else" — and an authority MUST either
complete the logon without prompting or deny it.

### The two exceptions this field carries

`supported_credential_types` is an optional trailing field, and it is
the only enumeration in this chapter whose unrecognised values are
dropped rather than refused. Both departures from §2.6 are deliberate,
and both are what make adding a credential type workable at all.

**An absent field means `Password`, not an empty list.** A decoder that
reaches the end of the body where this field would have been MUST read
it as a client supporting exactly the credential types that existed
before the field did — which is `Password`, and only `Password`. A
client predating the field could render nothing else. An absent field
and an explicitly empty one are therefore *different statements*, and an
implementation MUST NOT collapse them: the empty list is how a client
asks for a logon that requires no interaction, and reading it as
`Password` would turn that request into a prompt.

This is the one place where an empty length-framed field is not
equivalent to an absent one (§2.6).

**An unrecognised value is dropped, not refused.** A decoder MUST
discard a credential type it does not recognise and proceed with the
rest, leaving the intersection of what the client claims and what the
decoder understands. This is safe here and nowhere else, because the
field is a statement of capability rather than an instruction: an
authority that ignores a type it has never heard of merely declines to
use it, which is the correct outcome.

Without this, a client that learned a new credential type could not
speak to an older authority at all — the authority would be obliged by
§2.6 to refuse the whole message. The capability list exists precisely
so that an authority using a new type cannot reach an older client; it
would be self-defeating if a *client* using a new type could not reach
an older authority either.
