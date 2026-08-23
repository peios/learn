---
title: Enumerations
description: Every enumerated value the protocol carries — logon and identifier types, credentials, severities, denial codes, keys, kinds, fields and outcomes.
---

Adding a value to any enumeration here is a breaking change requiring a
version bump — see §2.6. The single exception is the field mask, noted
below.

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

The gaps are deliberate: the numbering follows KACS, and values it does
not define are not available here.

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

## Message severities

Carried in `Message.severity` (§2.8) as a `u8`.

| Value | Name |
|---|---|
| 0 | Info |
| 1 | Error |

## Denial codes

Carried in `AccessDenied.denial` (§2.10) as a `u32`.

| Value | Name | Meaning |
|---|---|---|
| 1 | `MalformedRequest` | The message could not be understood. |
| 2 | `UnsupportedVersion` | The protocol version is not implemented. |
| 3 | `PermissionDenied` | The peer may not originate this logon at all. |
| 4 | `AuthenticationFailed` | The principal is unknown, or the credential is wrong. Deliberately one code — see §2.10. |
| 5 | `LogonTypeNotPermitted` | The peer may not request this kind of session. |
| 6 | `AccountRestricted` | The principal exists and authenticated, but policy refuses this logon. |
| 7 | `AuthorityUnavailable` | The authority cannot reach what it needs to decide. |
| 8 | `ConversationLimit` | Too many rounds, or too long without an answer. |
| 9 | `Internal` | The authority failed for a reason it will not describe. |

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

This is the sole exception to the rule above. A bit MAY be added without
a version bump, because a reply states which fields it answered and an
authority MUST ignore a bit it does not implement (§2.16).

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
