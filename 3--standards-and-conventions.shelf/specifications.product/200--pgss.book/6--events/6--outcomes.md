---
title: Outcomes
description: One event type per action, with success and failure in outcome.success, outcome.reason, outcome.errno and outcome.detail, and what each of the four may carry.
---

An action that can succeed or fail is one event type, and its result is
carried in `outcome.*`. "Everything that failed" is then one query across
every emitter, and no descriptor can show an action's successes while
hiding its failures.

An emitter MUST NOT define separate event types for the success and the
failure of one action. A type that only ever records failure is
permitted (§6.3).

## The outcome fields

| Field | Type | Carries |
|---|---|---|
| `outcome.success` | `bool` | Whether the action did what was asked |
| `outcome.reason` | `str.enum` | Why it failed, or why a success was unusual |
| `outcome.errno` | `int.errno` | The error number it failed with |
| `outcome.detail` | `str` | Text for a person to read |

An event whose action can fail MUST carry `outcome.success`.

`outcome.reason` is symbolic. Its values are drawn from a named
reason-code family, or from an enumeration the event declares in its
fragment (§6.10). Where a kernel reason code exists for the decision, the
value is that code's name in kebab-case with its family prefix removed,
so that an event and a trace of the same decision describe it in the
same terms.

`outcome.errno` is the negative error number the operation returned,
`-13` for `EACCES`. It is omitted on success. A consumer renders it by
name.

`outcome.detail` is optional free text for a person. Nothing parses it,
and an emitter MUST NOT carry anything in it that a consumer would need
to filter on: that belongs in `outcome.reason` or in a field of its own.

Where a decision has more than two results, so that a boolean cannot
express it, `outcome.verdict` carries the result as an enumeration.

> [!NOTE]
> Before this chapter, the reason for one failure was written as
> `failure_reason`, `failure_cause`, `reason`, `error`, `detail`,
> `parse_error`, `finalization_detail`, `result` and `message`, and a
> descriptor denying one of them denied none of the others. The four
> fields above replace all nine.
