---
title: Identity and Authority
type: concept
description: Distinguish account records, runtime tokens, authentication sessions, and permission decisions.
---

An account record describes a principal. Authentication establishes which
principal is requesting a sign-in. A token carries the runtime identity and
authority used by a thread. An access decision combines that token with the
object, requested operation, and applicable policy. None of these steps is
interchangeable with the others.

## A name is not a grant

A security identifier (SID) identifies a principal. Resolved names are labels;
compare parsed binary identities rather than names or a domain prefix. A SID
alone does not reveal group membership, privileges, integrity, or whether an
account is signed in. Different accepted text spellings can represent the
same parsed SID; formatting differences alone do not establish inequality.

Use [PCDS's SID reference](~specifications/pcds/sid/binary-format) for encoding
and the [well-known catalog](~specifications/pcds/sid/well-known-sids) for
assigned identities. Avoid maintaining another numeric catalog in application
documentation.

For policy, distinguish the intended audience: Authenticated Users is not
Everyone, a service identity is not every process of its hosting account,
and a logon SID identifies one authentication context rather than the account
across sign-ins. Creator Owner is an inheritance placeholder; Owner Rights
controls the owner's special grants on the object being checked. Integrity
and process-trust labels belong to their mandatory-policy mechanisms, not
ordinary group membership.

## Accounts become runtime tokens

[Local account records](~peios/local-accounts/overview), source resolution,
and [authentication policy](~peios/authentication-policy/granting-access)
participate in sign-in. Token creation is privileged; the kernel does not
independently prove the truth of every claim a trusted creator supplies.
Changing an account record does not rewrite tokens already running.

A token carries a user SID, groups and their attributes, privileges,
integrity,
claims, restrictions, and session context. A privilege is a grant for specific
operations, not a substitute for identity. Integrity constrains categories of
access. Process Integrity Protection belongs to the executing program's PSB,
so impersonating another identity does not change program trust.

Claims are typed attributes. Token user/device claims, caller-supplied local
claims, and object resource attributes have different provenance. A missing
claim can evaluate to UNKNOWN: it does not satisfy a conditional allow and
can preserve a conditional denial. Do not substitute an empty value for
absence or treat a display label as a trusted claim. The [condition
specification](~specifications/pcds/security-descriptor/conditional-aces)
defines the logic.

## Follow the effective thread

A process's primary token is the default identity for its threads. A thread
handling a client can temporarily impersonate another token. Diagnose the
thread that performed the operation, not only the account displayed for the
process. Reverting returns to the primary token; it does not change the
process's program protection.

Token fields and operations are defined in the kernel's
[token model](~kernel/internals/kacs/tokens/the-token-model). Identity fields
cannot be arbitrarily relabeled by adjustment. Duplication, restriction,
privilege adjustment, and primary-token installation have different gates
and effects. A privilege can be disabled or removed; removal is not the same
as a reversible disable.

Fork gives the child an independent copy of the parent's primary token,
without inheriting an active impersonation. Threads share the primary token
but have independent impersonation state. Exec reverts impersonation and
normally retains the primary token, subject to the documented integrity
lowering rule. See [Token Lifecycle](~kernel/internals/kacs/tokens/token-lifecycle)
for installation convergence and exact transitions.

## Authentication sessions and elevation

A logon session records an authentication context shared by its tokens.
It is separate from a terminal's job-control session and from an interactive
environment scope. Do not use a boot-local session identifier as a durable
account identity or assume its value cannot recur on another boot.

A session's type records how it was created. Local console authentication,
remote SSH/GXWI sign-in, and service launch have different provenance.
The type is not a blanket access grant; token groups and specific kernel
operations give it effects. A NetworkCleartext name alone does not prove a
password traversed an unencrypted network, and NewCredentials metadata does
not implement an outbound credential broker by itself.

A linked Full/Limited pair is a kernel mechanism available to a trusted
broker. It does not establish that every interactive sign-in uses a pair,
that a consent interface exists, or that the caller can install its partner.
The role can remain after the active link disappears. Use the
[linked-token reference](~kernel/internals/kacs/tokens/linked-tokens-and-elevation)
and the actual broker's documented workflow.

Ending a session coordinates its processes; it does not revoke every token
handle held elsewhere. Token expiration metadata is not a kernel access-check
timer. Follow [Inspecting and Ending Sessions](~peios/system-and-processes/logonse)
for the supported command and its completeness limits.

## Privilege state and operation authority

A token can have a privilege present but disabled. Enabling a present
privilege is different from adding one; permanently removed privileges cannot
be re-enabled on that token. Enabled-by-default state is a creation property,
and the used bit records exercise rather than a timestamped use history.
Consult the [privilege model](~kernel/internals/kacs/privileges/the-privilege-model)
and [adjustment rules](~kernel/internals/kacs/tokens/token-adjustment) before
interpreting or changing those states.

Some privileges gate kernel operations directly, some contribute rights in
AccessCheck, some are interpreted by services, and some names are reserved.
A name in a catalog does not prove enforcement by every component. Backup and
restore contributions require the relevant intent as well as enabled
privileges; the object manager's actual open/update path supplies its own
context. PIP, confinement, and central policy can still constrain grants.
Removing privileges and adding restricting SIDs are separate reductions.
