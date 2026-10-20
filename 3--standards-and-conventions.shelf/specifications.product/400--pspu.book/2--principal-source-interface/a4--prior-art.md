---
title: Prior Art
description: The approaches PSI exists to avoid — in-process authentication packages above all — and the ones it adopts.
---

## What this exists to avoid

The design is shaped more by rejected approaches than adopted ones.

**LSA authentication packages.** Windows loads authentication packages
as DLLs into the LSA process. A defect in any package is a defect in the
most privileged process on the system, and the packages are exactly the
components most likely to parse hostile input. PSI puts that boundary at
a process, permanently: there is no in-process extension point and no
message that could create one.

**PAM modules.** The same objection, plus stacking — offering a
credential to each module in turn until one accepts, which hands every
module the credentials of every other module's users. PSI resolves
*which* source answers before any credential is collected (§2.11).

**NSS.** Name service switch modules answer "who is this?" as a library
call in whatever process asked, with no boundary at all. PSI's answer is
a message from a process that was separately identified.

## What is adopted

**RSI's shape**, specified in PSPK. A long-lived connection, sources
that dial in and register, multiplexed requests tagged with an
identifier, and the authority tearing down a connection it cannot parse.
PSI is recognisably the same family, and deliberately so — an
implementer who has written a registry source will find little
surprising here.

The differences are worth naming, because they follow from what is being
federated. A registry source is trusted with the correctness of a
subtree and the kernel validates its structure; a principal source is
trusted with identity, so the checks it faces are about *scope* — which
principals, which memberships, which numbers — rather than about
well-formedness alone. And the kernel assigns a registry source no
numeric range, because there is nothing to project.

**PGSS Logon's interrogation, wholesale.** Rather than inventing a
parallel vocabulary for prompts and answers, PSI relays PGSS Logon's
messages with identical bodies (§2.5). The gain is not brevity but
correctness: there is no translation layer to be lossy, and a source's
prompt reaches the client exactly as written.

## Design influences

**Sources connect inward.** The authority never dials out. See §2.3 —
this is the single most consequential shape decision in the chapter.

**Assertion, not minting.** The success terminal deliberately cannot
express a session or a token (§2.4). The separation is structural rather
than a rule an implementer must remember.

**Domains claimed, not assumed.** A source states what it is
authoritative for and the authority confines it to that (§2.10, §2.18).
The alternative — an authority that trusts whatever a source says about
anyone — makes every source as dangerous as the most dangerous one.

**Relative numbers.** POSIX identifiers are the one thing a source
states that has no namespace of its own to be confined by, so the range
supplies one (§2.20). Nothing else in the protocol needed inventing; a
SID already carries its domain.
