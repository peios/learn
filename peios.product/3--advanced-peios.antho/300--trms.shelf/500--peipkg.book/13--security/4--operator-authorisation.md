---
title: Operator Authorisation
description: The points requiring a deliberate act specific to the elevated action, why --yes does not satisfy them, and what is left ungated.
---

Several points call for **operator authorisation**: a deliberate,
explicit act specific to the elevated action in question, distinct from
the routine prompt to proceed, never inferred or defaulted, and recorded
in the audit stream.

## What is gated

| Elevated action | Gate |
|---|---|
| Downgrade | A per-action prompt, audited |
| A low-trust provider filling a high-trust role | A per-action prompt, audited |
| A foreign `replaces` against a higher-priority package | A per-action prompt, audited |
| Proceeding on stale trust state | The `--allow-stale` flag, audited, no prompt |
| Installing unsigned content under an `optional` policy | Warned per package on every operation; not gated, not audited |
| Enabling insecure transport | Not gated, not audited |
| Resolving an interrupted transaction | Not gated, not audited |

The three prompted actions are raised by the resolver as
authorizations, presented individually, and confirmed on their own
terms. The authorising act and what it authorised are recorded.

## `--yes` does not satisfy them

`--yes` confirms the routine "apply this plan?" prompt. Authorizations
are collected and confirmed **before** that prompt is reached, so
`--yes` satisfies none of them.

With input closed, an authorization prompt reads end-of-input and
returns a refusal, so a non-interactive invocation of an elevated action
cancels rather than proceeding. That is the right direction to fail.

## Confirming a specific action

The text interface displays the action's detail and requires a phrase
naming both the action and package. For example, downgrading `widget`
requires `authorise downgrade widget`, followed by a newline. The other
action names are `low-trust-provides` and `foreign-replaces`. Use the
phrase printed by the prompt; matching is case-sensitive, with surrounding
whitespace ignored.

A generic `y` or `yes` refuses an elevated action. The first refusal
cancels the plan, and each answer given is audited. End-of-input,
including an unterminated phrase, also refuses. `--yes` still skips only
the routine proceed prompt.

Scripts may supply these specific phrases through standard input; a
terminal is not required. This prevents a generic stream of affirmatives
from approving every gate, but is not proof of a human's presence or a
cryptographic authorisation. The structured driven interface continues to
accept a separate `yes` answer tied to each authorisation question's ID.

## Flags outside the frame

Three flags waive a check with a bare boolean and no authorisation
record: the path-restriction bypass, and — where they exist — a
critical-package override and an unowned-file overwrite. The first
touches the payload layout rules directly, and none of the three appears
in any audit event.

## Where this is going

The intended end state binds authorisation cryptographically: a fresh,
kernel-authenticated authorisation from a principal holding rights
beyond the operator's routine set, carrying the transaction identifier,
the full operation specification, a nonce, and a timestamp; validated by
the kernel rather than by peipkg; and emitted as an audit record
co-signed by the authorising principal, so the trail does not rest on
peipkg's own honesty.

That depends on kernel primitives that do not exist yet — an asymmetric
key bound to a token, and event-payload signature verification. Until
they do, authorisation is the deliberate act described above, and peipkg
does not present it as the stronger guarantee.
