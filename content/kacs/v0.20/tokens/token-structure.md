---
title: Token Structure
order: 1
description: Structure and contents of a KACS access token
---

A token is the kernel's representation of a security context. Every process MUST have an associated primary token. A process MAY additionally hold an impersonation token.

## Required fields

A conforming token MUST contain the following fields:

### User SID

The User SID identifies the principal the token represents. This MUST be a valid SID as defined in the SID specification.

### Group SIDs

A token MUST contain zero or more group SIDs. Each group SID SHOULD have associated attributes indicating whether the group is enabled for access checking.

### Privileges

A token MAY contain privileges. Each privilege MUST be identified by a LUID and MUST have an enabled/disabled state. An implementation MUST NOT grant access based on a disabled privilege.

## Integrity level

Every token MUST carry an integrity level. The integrity level MUST be one of: Untrusted, Low, Medium, High, or System.
