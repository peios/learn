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
| `required_credential_type` | `u8`; 0 none, 1 Password, 2 SshPublicKey | §2.D |
| `has_ssh_binding` | `u8`, exactly 0 or 1 | |
| `ssh_binding` | structure, present when the flag is 1 | §2.D |

Everything here is *asserted by the client*, and §2.4 governs all of it.

## logon_type

The kind of session the client is asking for. **A proposal**, which the
authority MUST constrain against the verified peer — see §2.4.

Values are defined by KACS and listed for reference in §2.B.

### The exception this field carries

A value MAY be added to this enumeration without a version bump. This is
the third departure from §2.6, and it turns on the same question that
rule turns on: which party has to understand the value. The rule binds
because every peer must understand every value it is *sent*, and
`logon_type` only ever travels client to authority. The authority is
therefore the only party that must understand a new one.

**An authority MUST refuse a `logon_type` it does not recognise**, with
`MalformedRequest` (§2.10). A message carrying a value the authority
cannot name is one it could not understand, and it is refused before
any question of what the peer is permitted arises.

Neither direction of mismatch is left to chance by that. An older client
never proposes a value it has not heard of, and a newer client proposing
one to an older authority is refused — so the failure is no session
rather than a session of the wrong kind, which is the outcome §2.6
exists to prevent.

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

### Mandatory capability and method fields

The capability list and following method/binding fields are mandatory in
the current unpublished version-1 layout. Missing tails are malformed;
there is no absent-field Password default. An explicit empty list means
that the client cannot collect a credential.

A nonzero required method must appear in the capability list. The authority
rejects any source assertion that did not authenticate with that method.
The SSH binding is present exactly when SshPublicKey is advertised. It is
an enclosing length-framed structure containing 16 raw connection-ID bytes,
a session-identifier byte string (16–64 bytes), and a UTF-8 username
(1–256 bytes, no controls), equal to the Username identifier byte for byte.
Only the authorized SSH monitor may supply it; see §2.D.

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
