---
title: Introduction
order: 1
description: Overview of the Kernel Access Control Subsystem
---

This specification defines the Kernel Access Control Subsystem (KACS) for the Peios operating system. KACS provides identity-aware, discretionary and mandatory access control at the kernel level.

## Scope

An implementation MUST support all features described in this specification to claim conformance. An implementation SHOULD provide meaningful error codes when denying access.

## Terminology

This specification uses the key words MUST, MUST NOT, SHALL, SHALL NOT, SHOULD, SHOULD NOT, MAY, and OPTIONAL as described in RFC 2119.

## Design principles

The access control model is built on three foundations:

1. **Identity** — every process carries a token describing who it acts as
2. **Descriptors** — every securable object carries a security descriptor defining access policy
3. **AccessCheck** — a single algorithm evaluates token against descriptor to produce an access decision
