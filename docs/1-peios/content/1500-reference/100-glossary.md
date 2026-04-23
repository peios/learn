---
title: Glossary
type: reference
description: Key terms and acronyms used throughout Peios security documentation.
---

## A

**ACE (Access Control Entry)** — A single rule in an access control list. Each ACE specifies a principal (by SID), an access mask, and whether the rule allows or denies. See [Access Control Lists](~peios/access-control/access-control-lists).

**AccessCheck** — The kernel function that evaluates every access decision. Takes a token, a security descriptor, and a desired access mask, and returns the granted rights or a denial. See [How AccessCheck Works](~peios/access-control/how-accesscheck-works).

**Access mask** — A 32-bit bitmask encoding the rights being requested, granted, or denied. Bits are divided into specific rights (object-type-dependent), standard rights, and generic rights. See [Access Masks and Rights](~peios/access-control/access-masks-and-rights).

## C

**CAP (Central Access Policy)** — An organization-wide policy that applies to objects based on resource attributes, evaluated as an additional intersection step in AccessCheck. See [Understanding Central Access Policy](~peios/central-access-policy/understanding-central-access-policy).

**Claim** — A name-value pair carried on a token (user claim) or derived from resource attributes, used in conditional ACE expressions for attribute-based access control. See [Claims and Attributes](~peios/conditional-access/claims-and-attributes).

**Confinement** — An application isolation model that inverts the default permission model. A confined process has zero access unless explicitly granted via confinement capability SIDs. See [Understanding Confinement](~peios/confinement/understanding-confinement).

**Conditional ACE** — An ACE with an embedded expression that evaluates token claims and resource attributes at access-check time. Enables attribute-based access control. See [Understanding Conditional ACEs](~peios/conditional-access/understanding-conditional-aces).

## D

**DACL (Discretionary Access Control List)** — The ordered list of ACEs in a security descriptor that determines who can access the object and what they can do. See [Access Control Lists](~peios/access-control/access-control-lists).

**Deny ACE** — An ACE that explicitly removes rights from a principal. Deny ACEs are evaluated before allow ACEs at the same inheritance level.

## F

**FACS (File Access Control Subsystem)** — The kernel subsystem that applies security descriptors to files and directories, replacing traditional Linux mode bits with the full SD model.

## G

**Generic rights** — Abstract access rights (GENERIC_READ, GENERIC_WRITE, GENERIC_EXECUTE, GENERIC_ALL) that are mapped to object-specific rights before evaluation. See [Access Masks and Rights](~peios/access-control/access-masks-and-rights).

## I

**Impersonation** — A mechanism where a thread temporarily assumes another principal's identity. The impersonation token replaces the thread's primary token for access decisions. See [Understanding Impersonation](~peios/impersonation/understanding-impersonation).

**Impersonation level** — Controls how far an impersonated identity can travel: Anonymous, Identification, Impersonation, or Delegation. See [Impersonation Levels](~peios/impersonation/impersonation-levels).

**Integrity level** — A trust tier assigned to tokens and objects. From lowest to highest: Untrusted, Low, Medium (default), High, System. See [Integrity Levels Explained](~peios/integrity/integrity-levels-explained).

## K

**KACS (Kernel Access Control Subsystem)** — The kernel module that implements the entire Peios security model: tokens, security descriptors, AccessCheck, MIC, PIP, confinement, auditing, and more.

## L

**Linked tokens** — A pair of tokens (filtered and elevated) created at logon for administrative users. The filtered token is used by default; the elevated token is used after explicit elevation. See [How Linked Tokens and Elevation Work](~peios/identity/linked-tokens-and-elevation).

**Logon session** — A kernel object representing a single authentication event, identified by a unique logon SID. See [Understanding Logon Sessions](~peios/identity/understanding-logon-sessions).

## M

**MIC (Mandatory Integrity Control)** — A mandatory access control layer that enforces the no-write-up rule: processes cannot modify objects labeled above their integrity level, regardless of DACL permissions. See [Understanding MIC](~peios/integrity/understanding-mic).

## O

**Owner** — The principal who owns an object. The owner implicitly receives READ_CONTROL and WRITE_DAC unless Owner Rights ACEs modify this default. See [Ownership and Owner Rights](~peios/access-control/ownership-and-owner-rights).

## P

**PIP (Process Integrity Protection)** — A protection mechanism for critical processes and objects that cannot be bypassed by privileges. Uses two dimensions: type (None, Protected, Isolated) and trust level (from binary signing). See [Understanding PIP](~peios/pip/understanding-pip).

**Primary token** — The process-level token inherited by all threads. Child processes receive a copy of their parent's primary token.

**Privilege** — A system-wide right carried on a token, separate from DACL access rights. Privileges gate specific operations (backup, shutdown, take ownership) and must be explicitly enabled before use. See [Understanding Privileges](~peios/privileges/understanding-privileges).

**Principal** — Any entity that can have an identity: a user, group, service, or machine. Each principal is identified by a unique SID.

## R

**Restricted token** — A token carrying additional restricting SIDs. AccessCheck runs a second DACL walk using only the restricting SIDs and intersects the result. See [Understanding Restricted Tokens](~peios/token-restriction/understanding-restricted-tokens).

## S

**SACL (System Access Control List)** — The portion of a security descriptor containing audit rules, mandatory integrity labels, PIP trust labels, resource attributes, and central policy references. Requires SeSecurityPrivilege to read or modify.

**SD (Security Descriptor)** — The complete security policy attached to an object: owner, primary group, DACL, and SACL. See [How Security Descriptors Work](~peios/access-control/how-security-descriptors-work).

**SID (Security Identifier)** — A globally unique, immutable identifier for a principal. Format: `S-1-authority-subauthority1-subauthority2-...`. See [What Are SIDs](~peios/identity/what-are-sids).

## T

**Token** — A kernel object carrying a thread's complete security context: user SID, group SIDs, privileges, integrity level, and impersonation state. The single source of identity for all access decisions. See [How Tokens Work](~peios/identity/how-tokens-work).

**Trust label** — A special ACE in the SACL that encodes an object's PIP protection level (type + trust). See [Understanding PIP](~peios/pip/understanding-pip).
