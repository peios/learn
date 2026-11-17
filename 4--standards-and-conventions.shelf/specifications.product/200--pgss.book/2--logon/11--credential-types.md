---
title: Credential Types
description: What a credential type tells a client to collect, why the registry is kept short, and why credentials cross the socket in the clear.
---

A credential type tells a client **how to collect** an answer. It does
not tell it what the answer means.

| Value | Name | Collection |
|---|---|---|
| 1 | Password | A line of text, not echoed |
| 2 | SshPublicKey | Bound SSH candidate or signature proof; §2.D |
| 3 | Mschapv2 | Relay a source-issued challenge and typed password proof |
| 4 | Ntlmv2 | Relay an authority-issued challenge; the answer names the principal |

The registry is deliberately short. A type is added when a client would
need to collect something differently, not when an authority acquires a
new way of checking something.

> [!NOTE]
> A one-time code is collected exactly as a password is — a line of
> text, not echoed — so it needs no new type. An authority asks for it
> with `credential_type = Password` and a `credential_name` of
> "Verification code". A hardware token that requires a challenge to be
> relayed to a reader *would* need a new type, because no existing
> collection method produces the answer.
>
> This is the test to apply: does an existing client, understanding only
> the types it already has, collect the right thing? If yes, no new type
> is needed.

## Adding a type

The initial unpublished type-2 extension replaced the version-1 layout
and all consumers together (§2.D). Future incompatible changes to a
published contract require the version discipline in §2.6.

An authority MUST NOT send a prompt for a type absent from the client's
`supported_credential_types`, so an authority using a new type simply
cannot reach an older client — which is the correct outcome, and is why
the capability list exists. The converse — a newer *client* reaching an
older authority — is what the dropping rule in §2.7 exists for.

## MSCHAPv2 collection

A Mschapv2 prompt MUST carry exactly 16 bytes in `parameters`: the
source-issued authenticator challenge. Its answer MUST contain exactly
40 bytes, peer challenge (16 bytes) followed by NT response (24 bytes).
The originator relays this exchange inside its authenticated TLS tunnel;
it MUST NOT substitute a password prompt or supply a stored NT hash.

Verification follows RFC 2759. The source binds the challenge to the
account, credential revision and bounded conversation, and rechecks
current eligibility before asserting success. ChallengeHash uses the
exact wire username spelling, excluding any domain prefix as required
by RFC 2759; account-name lookup equivalence does not change those bytes.
MSCHAPv2 proves the account password through a different mechanism and
MUST follow the source's password-authentication eligibility policy.

A successful general authentication returns the 20-byte binary
AuthenticatorResponse in `mschapv2_success` (§2.24). The source MUST NOT
export its reusable NT hash. Credential storage and opportunistic
population of NT material remain source policy, not collection protocol.

## NTLMv2 collection

Ntlmv2 is the only **identity-in-answer** type. NTLM sends its challenge
before the client names the principal, so the principal is known only
from the answer. The rules in this section depart from the conversation's
usual order for that reason, and apply to no other type.

An Ntlmv2 request MUST carry an empty identifier and MUST require Ntlmv2
(§2.24). An authority MUST refuse, as malformed, an Ntlmv2 request that
names a principal, advertises Ntlmv2 without requiring it, or advertises
any other type alongside it.

### The challenge

The **authority** issues the challenge, not a source. It MUST generate
eight bytes from a cryptographically secure random source, send them as
the `parameters` of a single Ntlmv2 prompt, and accept exactly one
answer to that prompt. A challenge MUST NOT be reused, MUST be discarded
when the conversation ends, and is never returned in any result.

An originator relays the challenge as the NTLM `ServerChallenge`. It MUST
NOT substitute a challenge of its own, and MUST NOT supply a stored NT
hash or a password in place of the client's proof.

### The answer

The answer's `data` is this structure:

| Field | Encoding | Limit |
|---|---|---|
| `user` | length-framed bytes, UTF-16LE | 2–512 bytes |
| `domain` | length-framed bytes, UTF-16LE | 0–512 bytes |
| `nt_response` | length-framed bytes | 48–4096 bytes |

`user` and `domain` are the `UserName` and `DomainName` of the NTLM
AUTHENTICATE message, byte for byte. `nt_response` is its
`NtChallengeResponse`: the 16-byte `NTProofStr` followed by the
`NTLMv2_CLIENT_CHALLENGE` structure, whose `RespType` and `HiRespType`
MUST both be 1. An odd length, an unpaired surrogate, or an empty `user`
is malformed. Anonymous NTLM, which has an empty user and response, is
not supported. The LMv2 response is not carried; NTLMv2 does not need it.

### Naming the principal

The authority decodes `user` to UTF-8 and applies §2.15 to it, with the
same refusals as any other identifier. While this specification defines
no realm syntax, `domain` selects no source: the authority MUST route on
the decoded user alone, and SHOULD record `domain` in its audit trail.

Ignoring the domain for routing does not weaken the proof. The client
binds `domain` into `ResponseKeyNT`, and the source verifies with the
bytes it received, so the domain the client used is still the domain it
proved. Clients fill it in unpredictably: often with the name the user
typed before a backslash, and sometimes with a name of the client's own
choosing. A server that refused unfamiliar domains would refuse those
clients and gain nothing in return.

The authority then routes on the decoded user exactly as it routes an
identifier (§2.15), and offers the challenge and answer to that one
source. It MUST NOT offer them to any other source, including when the
owning source fails or is unavailable.

### Verification

The source verifies the answer by MS-NLMP §3.3.2, using its stored NT
hash for the principal:

- `ResponseKeyNT` is HMAC-MD5 keyed with the NT hash, over the UTF-16LE
  concatenation of the uppercased `user` and `domain`. §2.15 limits
  names to printable ASCII, so ASCII uppercasing is what matters; any
  other code unit uses its Unicode simple uppercase mapping, as the
  closest available approximation of a Windows client. `domain` is used
  exactly as received.
- The expected `NTProofStr` is HMAC-MD5 keyed with `ResponseKeyNT`, over
  the challenge followed by `nt_response` after its first 16 bytes. The
  comparison MUST take constant time.
- On success, `SessionBaseKey` is HMAC-MD5 keyed with `ResponseKeyNT`,
  over `NTProofStr`.

The source binds the proof to the account and credential revision, and
rechecks current eligibility, as for MSCHAPv2. NTLMv2 proves the account
password through a different mechanism and MUST follow the source's
password-authentication eligibility policy.

A successful result carries the 16-byte `SessionBaseKey` in
`ntlmv2_session_key` (§2.9, §2.24). It is derived for this exchange
alone, cannot be used to authenticate again, and is what the originator
needs for NTLM key exchange and SMB signing. The source MUST NOT export
its NT hash or `ResponseKeyNT`.

The originator, not the authority or source, processes the rest of the
NTLM exchange: key exchange, the message integrity code, and the
`AvPairs` the client returned. Because those pairs sit inside the proven
`nt_response`, an originator MAY rely on them once the result arrives.

## Why passwords cross the local socket in the clear

Passwords travel this local socket as **plaintext**. SSH public-key
authentication instead carries public keys and signatures; private keys
never cross it. Remote SSH transport encrypts both authentication methods.
The local password choice allows the source to retain a memory-hard
password verifier without requiring a password-equivalent secret.
An optional MSCHAPv2-compatible source deliberately accepts that storage
trade-off for compatibility with remote challenge-response clients.

Challenge-response requires the verifier to store something it can
recompute the response from: either the plaintext, or a value that is
*password-equivalent*. NTLM works exactly this way — the stored hash is
as good as the password, forever, which is why pass-the-hash has been
the most valuable credential on a Windows network for twenty years.

A modern verifier — argon2id and its relatives — is deliberately **not**
password-equivalent and cannot answer a challenge. That is the property
that makes stealing the store meaningfully weaker than knowing the
passwords.

So challenge-response would trade a permanent weakness at rest for
protection of a channel that is not the weak point. Anyone able to read
this socket can already `ptrace` the process holding the password.

### What would change the answer

A PAKE — OPAQUE, SRP — gives both properties at once: nothing
password-equivalent at rest, and no plaintext on the wire. It is worth
revisiting if an authority ever authenticates **across a network without
TLS**.

It is not worth its complexity for a local, kernel-mediated socket,
where the threat it defends against is already able to do worse.

### What follows

Because plaintext crosses the wire, bounding how long it survives
becomes an obligation of both roles rather than a nicety. See §2.12.
