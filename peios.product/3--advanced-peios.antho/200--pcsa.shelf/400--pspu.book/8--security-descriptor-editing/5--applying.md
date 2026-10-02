---
title: Applying
description: The editor sends the whole descriptor and which components changed, only when the person says to; the requester applies exactly those, and answers once.
---

## `apply`

When the person asks for what they have done to take effect — Apply,
or OK — the editor sends:

| Member | Type | Meaning |
|---|---|---|
| `type` | `"apply"` | |
| `sd` | string | The whole descriptor as the person now has it, self-relative and in base64 as in the request (§8.4). |
| `parts` | array of strings | The components of `sd` that changed since the request, or since the last `apply` the requester answered `applied`: some of `owner`, `group`, `dacl`, `sacl`. |

The editor MUST NOT send an `apply` as the person changes things, only
when they ask for it. A descriptor applied part way through a change
can take away the access the person needs to finish it: denying
Everyone before granting oneself, say.

The editor MUST NOT name `owner` in `parts` unless the request's
`can.owner` was true, nor `sacl` unless `can.audit` was. It MUST NOT
send an `apply` while one is unanswered, and SHOULD NOT send one whose
`parts` is empty.

## The answer

The requester MUST answer every `apply` with exactly one line, in the
order they came:

| Line | Meaning |
|---|---|
| `{"type":"applied"}` | Every component in `parts` was applied. |
| `{"type":"failed","why":"…"}` | None was, or not all, and `why` says why, as text for the person. |

The requester MUST apply the components named in `parts`, and MUST NOT
apply any other component of `sd`. The rest is as the requester sent
it, or as the editor could not read it, and writing it back would at
best change nothing and at worst write over what changed meanwhile.

The requester SHOULD apply the named components in one operation where
the kind of object allows it. Where it cannot, and some were applied
and some were not, it MUST answer `failed` and SHOULD say which were
applied.

`why` is shown to the person as it stands. It SHOULD say what was in
the way in words they can act on — "you are not allowed to" — rather
than an error code.

## After the answer

On `applied`, the editor takes what it sent as the descriptor it is
editing from then on: a later `apply` names only what changed after.
If the person had asked to apply and close, the editor ends (§8.3).

On `failed`, the editor MUST show the person `why` and MUST NOT end
because of it: what they did is still there to be put right or
abandoned. What it has not had answered `applied` it still counts as
changed.
