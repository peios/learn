---
title: General Authentication
description: Verify credentials and disclose identity without creating a local token or session.
---

Authenticate and Logon share credential collection and identity validation.
Authenticate MUST NOT create an OS token, logon session or local user
environment. Its result is identity data, not a bearer credential, and MUST
NOT be accepted as a later request to issue a token.

The authority MUST establish the caller from the connected socket's token.
It MUST authorize the operation, requested groups and explicitly named claims
before collecting credentials. Unauthorized named disclosure MUST refuse the
request with PermissionDenied. AllPermitted instead requests the readable
subset and MUST preserve the distinction between absence and nondisclosure.

## Shared AuthenticationRequest

This length-framed structure is shared by AuthenticateStart, LogonStart
(§2.7) and source authentication. It has no message header.

| Field | Encoding | Limit |
|---|---|---|
| identifier_type | u8 | §2.B |
| identifier | length-framed opaque bytes | 1024 bytes |
| supported_credential_types | length-framed bytes, one u8 per type | 32 entries |
| required_credential_type | u8; zero means none | §2.D |
| has_ssh_binding | u8, exactly 0 or 1 | |
| ssh_binding | nested length-framed structure, when present | §2.D |

Supported types bind what the caller can collect. A required type MUST be
supported and MUST have been verified for success. Advertising Password alone
does not exclude an intentional no-credential account. A password-based access
service using plaintext password verification MUST require Password. An
MSCHAPv2 originator MUST require Mschapv2 instead. An NTLMv2 originator
MUST require Ntlmv2, advertise only Ntlmv2, and send an empty identifier;
the principal is named by the answer (§2.11). SSH binding and
authorized-originator checks remain those of §2.D.

## AuthenticateStart

Message type 0x0004, client to authority, first on /run/logon.sock.

| Field | Encoding | Limit |
|---|---|---|
| authentication | nested AuthenticationRequest | above |
| groups | u8, exactly 0 or 1 | |
| claim_selection | u8: 0 None, 1 Named, 2 AllPermitted | |
| claims | count and length-framed name entries, only for Named | 1–64 entries |

Each name entry contains one string of 1–255 UTF-8 bytes, without NUL.
Names compare using KACS's per-character Unicode lowercase mapping. This is
locale-independent, without Unicode normalization or full case folding:
Équipe and équipe are equivalent; ß and ss are not. Original spelling MUST
be preserved in returned claims. This rule applies to requested names,
source/result duplicate detection and named absence assertions.
Duplicate equivalent names MUST be refused as malformed.
None and AllPermitted carry no name array, including no zero count.

The authority uses CredentialRequest and CredentialResponse (§2.8), with the
same limits, cancellation and failure handling as Logon. Shared authentication
includes source routing, general account and credential checks, and validation
of source identity, memberships and typed claims. Local logon-type restrictions,
token privileges, POSIX projection and local setup belong to Logon finalization.

## Authenticated

Message type 0x8004, authority to client, terminal success.

| Field | Encoding | Limit |
|---|---|---|
| user_sid | length-framed SID bytes | 68 bytes |
| canonical_name | string | 256 bytes |
| verified_credentials | length-framed bytes, one u8 per verified type | 32 entries |
| has_groups | u8, exactly 0 or 1 | |
| groups | count and length-framed entries, only when has_groups is 1 | 1024 entries |
| claim_coverage | u8: 0 None, 1 Named, 2 Complete, 3 Filtered | |
| claims | existing typed claim array (§2.16) | 64 entries |
| absent_claims | count and length-framed name entries | 64 entries |
| mschapv2_success | length-framed bytes | 0 or 20 bytes |
| ntlmv2_session_key | length-framed bytes | 0 or 16 bytes |
| operation_guid | optional trailing byte string (§2.6) | 0 or 16 bytes |
| credential_binding | optional trailing byte string | exactly 32 bytes if present |

`mschapv2_success` MUST contain exactly 20 bytes if Mschapv2 is verified
and MUST be empty otherwise. It is the exchange-specific server
AuthenticatorResponse, not a reusable credential or an OS token.
`ntlmv2_session_key` MUST contain exactly 16 bytes, the NTLM
`SessionBaseKey`, if Ntlmv2 is verified and MUST be empty otherwise
(§2.11). Clients MUST reject missing or unexpected method output. These
outputs use the existing authentication grant; they introduce no separate
permission.

`credential_binding` is reference `[16]` followed by revision `[16]`, as in
§2.16. It names the credential actually verified, scoped to the verified SID
and source. An authority MUST obtain it from that validated source assertion,
not from a later unrelated lookup. No-credential success MUST omit it. Older
sources or authorities can omit it; absence means unknown metadata, never
evidence that the credential was deleted. The binding grants no authority.

This additive extension follows `operation_guid`. An authority emitting a
binding without a diagnostic GUID MUST emit the explicit empty GUID field
first. It MUST NOT move the established diagnostic slot. A malformed GUID
alone MUST NOT turn a valid authentication into failure; when its framing
cannot locate a later binding safely, the binding remains unknown. A present
malformed binding is a protocol error. Existing readers skip appended fields
through the body length. Public framing remains version 6.

Each group entry contains one length-framed SID byte string. All SIDs MUST be
structurally valid. Groups MUST be complete validated source memberships,
without duplicates or locally synthesized token groups. has_groups MUST equal
the request flag; an unrequested set differs from a complete empty set.

For Named selection, each requested claim MUST occur exactly once, either in claims or
absent_claims, using the same name equivalence. No unrequested claim may be
returned. Absence means authorized but not asserted; it differs from a
permission failure. Claim names and values retain §2.16's bounds and types.

None selection MUST return None coverage with empty claims and absent_claims.
Named selection MUST return Named coverage. AllPermitted MUST return Complete
or Filtered coverage, readable claim values and an empty absent_claims array.
It MUST NOT disclose restricted names or counts. Duplicate equivalent returned
names MUST be rejected for every mode.

Complete guarantees the entire source claim set was disclosed and policy
permits disclosure throughout the claim namespace. An omitted name is then
known absent. Filtered means policy may withhold names; omission alone is
unknown, not absence. Coverage MUST depend on disclosure authorization rather
than whether this particular principal actually has a restricted claim. If
the authority cannot establish complete namespace disclosure safely, it MUST
report Filtered. A consumer MUST NOT grant access from a condition requiring
unknown information.

verified_credentials lists checks actually completed, without duplicates.
Every entry MUST be understood and supported by the request. An empty list
means deliberate source-authorized no-credential success; it MUST NOT satisfy
a nonzero required_credential_type.

Authenticated MUST NOT carry a descriptor through SCM_RIGHTS. A client MUST
close and reject any received descriptor, incomplete disclosure, or result
that fails the required proof. Failure uses AccessDenied (§2.10).

## Local policy

Authd implements operation and disclosure authorization using the
AuthenticationSecurity descriptor under Machine\Generic\Authn\Policy.
Authenticate (0x1), Logon (0x2), ReadGroups (0x4) and ReadClaim (0x8)
are distinct rights. ReadClaim object ACEs target a deterministic claim GUID.
Claim-specific ACEs do not grant or deny root operation or group rights,
including through generic access masks.
See authd's registry manual for namespace, canonicalization, capability
assignment, defaults and administration.

Claim-read policy also applies to identity lookup and enumeration (§2.16).
Those requests ask for the complete claims field and do not collect a
credential. Authenticate can request named claims and authorize that selection
before collecting credentials, or request AllPermitted with coverage metadata.
Public identity and membership
lookup does not require Authenticate's ReadGroups grant.

ServiceAttest remains a separate PID-1-only path (§2.19). Authenticating a
principal does not grant authority to impersonate them or provision capabilities.
