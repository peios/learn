---
title: Private Layers
description: A disabled layer attached to a thread's credentials — how it resolves, how it is attached, and the privilege that is deliberately not checked.
---

A private layer is a **disabled** layer attached to a thread's
credentials. It is invisible during ordinary resolution and treated as
enabled when resolving on behalf of a thread whose token names it.

That covers three things a shared registry otherwise cannot do: giving
one session experimental settings without affecting others; injecting
test configuration without touching the shared tree; and giving a
container a different view of the registry without a separate hive.

## Resolution

A private layer participates in normal precedence ordering. A disabled
layer with precedence 5 attached to a thread resolves at precedence 5,
competing with everything else at that level. It is not an overlay on
top; it is a layer that only that thread can see.

The activity test is exactly: a layer is active for a thread if it is
globally enabled, or its name appears in that thread's private layer
set. Name matching uses Unicode Simple Case Folding, like every other
layer name comparison.

## Attachment

Private layer names reach a thread through the KACS token's LCS
credential extension — the same versioned block that carries scope
GUIDs for private hives (§5.2.2). LCS reads the credentials from the
effective token on each operation and passes them into resolution.

Private layers are therefore **per-thread, not per-process**: threads
in one process can hold different private layer sets through different
impersonation tokens.

## Two things about the caps

`MaxPrivateLayersPerToken`, default 16, is described as a limit on
attachment. It is not enforced there. KACS applies its own hard cap of
256 names when it parses the token specification, and the configurable
LCS limit is applied later, when LCS acquires a thread's private
credentials for an operation.

The consequence is that a token carrying seventeen private layers is
accepted by KACS and then fails every LCS operation with `EACCES`,
rather than being refused when it was built.

KACS also deduplicates private layer names using ASCII case-insensitive
comparison, where LCS matches them with Unicode Simple Case Folding.
Two names that LCS would treat as one layer can both sit on a token.

## The privilege that is not checked

Attaching a private layer whose precedence is above 0 ought to require
`SeTcbPrivilege` — otherwise an unprivileged process can attach an
existing high-precedence disabled layer to its own credentials and see,
and potentially influence, Group Policy-tier configuration.

**That check does not exist.** KACS never consults the LCS layer table
when parsing the credential extension, and there is no precedence
lookup and no privilege test anywhere on the attachment path. What does
gate attachment is `SeCreateTokenPrivilege`, because private layer
names can only enter a token when the token is created — the same
blanket gate that governs scope GUIDs.
