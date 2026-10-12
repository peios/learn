---
title: Private Layers
description: A disabled layer attached to a thread's credentials — how it resolves, how it is attached, and the authority retained from its creator.
---

A private layer is a **disabled** layer attached to a thread's
credentials. It is invisible during ordinary resolution and treated as
enabled when resolving on behalf of a thread whose token names it. [*layer.private.disabled-layer-active-for-a-naming-thread]

That covers three things a shared registry otherwise cannot do: giving
one session experimental settings without affecting others; injecting
test configuration without touching the shared tree; and giving a
container a different view of the registry without a separate hive.

## Resolution

A private layer participates in normal precedence ordering. [*layer.private.participates-in-normal-precedence] A disabled
layer with precedence 5 attached to a thread resolves at precedence 5,
competing with everything else at that level. It is not an overlay on
top; it is a layer that only that thread can see.

After private-attachment authorization succeeds, a layer is active for a
thread if it is globally enabled, or its name appears in that thread's
private layer set. [*layer.private.activity-test]

Name matching uses Unicode Simple Case Folding, like every other layer
name comparison. [*layer.private.names-matched-by-case-folding]

## Attachment

Private layer names reach a thread through the KACS token's LCS
credential extension — the same versioned block that carries scope
GUIDs for private hives (§5.2.2). [*layer.private.names-come-from-the-token-credential-extension]

LCS reads the credentials from the effective token on each operation
and passes them into resolution. [*layer.private.credentials-read-from-the-effective-token-per-operation]

Private layers are therefore **per-thread, not per-process**: threads
in one process can hold different private layer sets through different
impersonation tokens. [*layer.private.are-per-thread-not-per-process]

## Two things about the caps

`MaxPrivateLayersPerToken`, default 16, is described as a limit on
attachment. [*layer.private.max-private-layers-per-token-default-16] It is not enforced there. [*layer.private.cap-not-enforced-at-attachment]

KACS applies its own hard cap of 256 names when it parses the token
specification. [*layer.private.kacs-hard-cap-of-256-at-parse] The configurable LCS limit is applied later, when
LCS acquires a thread's private credentials for an operation. [*layer.private.lcs-cap-applied-at-credential-acquisition]

The consequence is that a token carrying seventeen private layers is
accepted by KACS and then fails every LCS operation, rather than being
refused when it was built. [*layer.private.over-cap-token-accepted-then-fails-every-operation] Reading LCS's configured limits from KACS
would invert the dependency between the two, so the cap stays where it
can be read.

The failure is `E2BIG`. [*layer.private.over-cap-is-e2big] It was `EACCES`, which read as an access-control
denial and sent anyone debugging it towards descriptors and privileges
rather than towards a count that was fixed when the token was assembled,
possibly in another process.

`MaxScopeGUIDsPerToken` shares the check and the errno. [*layer.private.max-scope-guids-shares-the-check-and-errno] A missing token
is still `EACCES`, because that one is an access decision. [*layer.private.missing-token-is-eacces]

KACS deduplicates the private layer names it parses with the same
Unicode Simple Case Folding LCS matches them by, so a name that LCS
treats as one layer is one layer here too. [*layer.private.kacs-dedupes-names-by-case-folding]

It did not always: an ASCII case-insensitive comparison let two names
differing only in a non-ASCII case relation — `ROLEs` and `roles`, since
U+017F folds to `s` — both sit on one token, spending two of the token's
`MaxPrivateLayersPerToken` slots on a single layer. Resolution still
folded correctly on the LCS side, so the layer activated once, but the
two sides of one identity contract disagreed.

## Attachment authority

Private-layer names can enter a token only at creation, which requires
`SeCreateTokenPrivilege`. [*layer.private.attachment-gated-by-secreatetokenprivilege]
Attaching a known layer above precedence 0 additionally requires enabled
`SeTcbPrivilege` on the **creator**. Without it, creation fails with `EPERM`,
even when the requested child token itself includes TCB privilege. A present
but disabled privilege does not authorize attachment.

The kernel retains the creator's authorization as immutable token state.
A trusted creator can delegate a private high-precedence view to an ordinary
token without giving the consumer TCB privilege. Duplication, restriction,
process propagation and impersonation preserve that attachment authority;
they do not obtain new authority from the duplicating caller.
[*layer.private.tcb-authorized-attachment-can-be-delegated]

Layer names need not exist when attached, and precedence can change later.
For each operation acquiring private credentials, LCS checks the retained
authority against the **same layer snapshot** used for resolution. If an
attachment made without TCB authorization now names a layer above precedence
0, the operation fails with `EPERM`. It does not silently choose a lower
layer. This applies to queries through already-open key handles as well as
new opens; a later promotion or creation cannot upgrade the attachment.
Returning the layer to precedence 0 makes the original attachment usable
again. Ordinary key and layer access checks still apply.

KACS invokes an LCS-supplied validator before exposing a newly created token.
The callback is installed during kernel initialization and then read-only;
a private extension cannot be published without its validator. LCS owns the
layer lookup, so KACS does not interpret the layer table. Use-time validation
closes the race between the creation check and a concurrent metadata change.
Successful TCB authorization marks the privilege used on the creator.

This is the PEI-268 behavior; older kernels lack the attachment check.
