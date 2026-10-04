---
title: Enumerations
description: Every enumerated value the protocol carries — logon and identifier types, credentials, severities, denial codes, keys, kinds, fields and outcomes.
---

Adding a value to any enumeration here is a breaking change requiring a
version bump — see §2.6, which states the four exceptions and where
each is stated in full.

## Logon types

Carried in `LogonStart.logon_type` (§2.7) as a `u8`. Semantics are
defined by KACS and described in the Peios Kernel TRM; this table is for
reference.

| Value | Name |
|---|---|
| 2 | Interactive |
| 3 | Network |
| 4 | Batch |
| 5 | Service |
| 8 | NetworkCleartext |
| 9 | NewCredentials |
| 10 | RemoteInteractive |

The gaps are deliberate: the numbering follows KACS, and values it does
not define are not available here.

A value MAY be added here without a version bump, for the reason §2.7
gives.

## Identifier types

Carried in `LogonStart.identifier_type` (§2.7) as a `u8`.

| Value | Name | `identifier` holds |
|---|---|---|
| 1 | Username | A principal name |

## Credential types

Carried in `Prompt.credential_type` (§2.8) and in
`LogonStart.supported_credential_types` (§2.7) as a `u8`. See §2.11 for
when a new one is warranted.

| Value | Name | Collection |
|---|---|---|
| 1 | Password | A line of text, not echoed |
| 2 | SshPublicKey | Bound SSH candidate or signature proof; §2.D |

## Message severities

Carried in `Message.severity` (§2.8) as a `u8`.

| Value | Name |
|---|---|
| 0 | Info |
| 1 | Error |

## Enrolment actions

Carried in `CredentialEnrollStart.action` (§2.23) as a `u8`.

| Value | Name | `material` holds |
|---|---|---|
| 1 | `Add` | The credential to enrol: for `SshPublicKey`, one line of an OpenSSH public key file |
| 2 | `Remove` | Which credential to remove: for `SshPublicKey`, its `SHA256:` fingerprint |

`CredentialEnrollStart.credential_type` takes a value from the
credential types above; only `SshPublicKey` is defined for enrolment.

## Denial codes

Carried in `AccessDenied.denial` (§2.10) as a `u32`.

| Value | Name | Meaning |
|---|---|---|
| 1 | `MalformedRequest` | The message could not be understood. |
| 2 | `UnsupportedVersion` | The protocol version is not implemented. |
| 3 | `PermissionDenied` | The peer may not make this request at all. |
| 4 | `AuthenticationFailed` | The principal is unknown, or the credential is wrong. Deliberately one code — see §2.10. |
| 5 | `LogonTypeNotPermitted` | The peer may not request this kind of session. |
| 6 | `AccountRestricted` | The principal exists and authenticated, but policy refuses this logon; or, in a credential change, the principal has no credential that can be changed (§2.20). |
| 7 | `AuthorityUnavailable` | The authority cannot reach what it needs to decide. |
| 8 | `ConversationLimit` | Too many rounds, or too long without an answer. |
| 9 | `Internal` | The authority failed for a reason it will not describe. |
| 10 | `NoSuchSession` | There is no live logon session by that identifier. Answers only `SessionEnd` and `SessionEndQuery` (§2.22). |
| 11 | `CredentialRejected` | The credential offered for enrolment, or named for removal, was refused: unreadable, unsupported, already held, one too many, or not held. Answers only `CredentialEnrollStart` (§2.23). |

A denial code MAY be added without a version bump where it only ever
answers messages newer than it is — messages no peer that predates the
code can send — because such a peer is then never sent it. `NoSuchSession`
and `CredentialRejected` were added under this rule. A client of the newer messages SHOULD treat a
code it does not recognise as a refusal, reporting the code and
`reason`, rather than as an unreadable answer; it is the one place in
this chapter where a client may meet a denial newer than itself.

## Key types

Carried in `Lookup.key_type` (§2.16) and `Enumerate.of_key_type`
(§2.17) as a `u8`. Zero in `of_key_type` means the field is unused.

| Value | Name | Key is in |
|---|---|---|
| 1 | `Name` | `name` |
| 2 | `Sid` | `sid` |
| 3 | `UnixId` | `unix_id` |

## Object kinds

Carried in `Lookup.kind`, `LookupReply.kind_found` and `Enumerate.kind`
(§2.16, §2.17) as a `u8`.

| Value | Name |
|---|---|
| 0 | `Any` |
| 1 | `Principal` |
| 2 | `Group` |

`Any` is not valid in `kind_found` or in `Enumerate.kind`.

## Fields

Carried in `Lookup.fields`, `Enumerate.fields` and `LookupReply.present`
(§2.16) as a `u32` bitmask, and in a withheld entry's `field` as a
single bit.

| Bit | Name | Value encoding |
|---|---|---|
| 0 | `UNIX_ID` | `u32` |
| 1 | `PRIMARY_GROUP` | reference |
| 2 | `HOME` | string |
| 3 | `SHELL` | string |
| 4 | `DISPLAY_NAME` | string |
| 5 | `GROUPS` | array of references |
| 6 | `MEMBERS` | array of references |
| 7 | `CLAIMS` | array of claim entries |
| 8 | `ENABLED` | `u8` |
| 9 | `LOGON_TYPES` | `u32` |
| 10 | `DESCRIPTION` | string |

A bit MAY be added without a version bump, because a reply states which
fields it answered and an authority MUST ignore a bit it does not
implement (§2.16).

## Lookup outcomes

Carried in `LookupReply.outcome` and `EnumerateReply.outcome` (§2.18) as
a `u8`.

| Value | Name |
|---|---|
| 1 | `Found` |
| 2 | `NotFound` |
| 3 | `Unavailable` |
| 4 | `Refused` |
| 5 | `Malformed` |

## Withheld reasons

Carried in a withheld entry's `reason` (§2.16) as a `u8`.

| Value | Name | Meaning |
|---|---|---|
| 1 | `Absent` | The field has no value. |
| 2 | `Restricted` | The caller may not have this field. |
| 3 | `Declined` | The source will not produce it. |
| 4 | `TooLarge` | It exists and exceeds one reply; use `Enumerate` (§2.17). |
