---
title: General Authentication
description: Verify credentials and disclose identity without creating a local token or session.
---

Authenticate and Logon share credential collection and identity validation.
Authenticate MUST NOT create an OS token, logon session or local user
environment. Its result is identity data, not a bearer credential, and MUST
NOT be accepted as a later request to issue a token.

The authority MUST establish the caller from the connected socket's token.
It MUST authorize the operation and every requested disclosure before
collecting credentials. Unauthorized disclosure MUST refuse the request with
PermissionDenied; silent omission is not a substitute.

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
service MUST require Password. SSH binding and authorized-originator checks
remain those of §2.D.

## AuthenticateStart

Message type 0x0004, client to authority, first on /run/logon.sock.

| Field | Encoding | Limit |
|---|---|---|
| authentication | nested AuthenticationRequest | above |
| groups | u8, exactly 0 or 1 | |
| claims | count and length-framed name entries | 64 entries |

Each name entry contains one string of 1–255 UTF-8 bytes, without NUL.
ASCII letters compare case-insensitively; non-ASCII bytes compare exactly.
Duplicate equivalent names MUST be refused as malformed.

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
| claims | existing typed claim array (§2.16) | 64 entries |
| absent_claims | count and length-framed name entries | 64 entries |

Each group entry contains one length-framed SID byte string. All SIDs MUST be
structurally valid. Groups MUST be complete validated source memberships,
without duplicates or locally synthesized token groups. has_groups MUST equal
the request flag; an unrequested set differs from a complete empty set.

Each requested claim MUST occur exactly once, either in claims or
absent_claims, using the same name equivalence. No unrequested claim may be
returned. Absence means authorized but not asserted; it differs from a
permission failure. Claim names and values retain §2.16's bounds and types.

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
See authd's registry manual for namespace, canonicalization, capability
assignment, defaults and administration.

Claim-read policy also applies to identity lookup and enumeration (§2.16).
Those requests ask for the complete claims field and do not collect a
credential. Authenticate instead requests named claims and authorizes that
selection before collecting credentials. Public identity and membership
lookup does not require Authenticate's ReadGroups grant.

ServiceAttest remains a separate PID-1-only path (§2.19). Authenticating a
principal does not grant authority to impersonate them or provision capabilities.
