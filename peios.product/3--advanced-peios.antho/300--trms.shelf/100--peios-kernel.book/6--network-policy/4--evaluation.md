---
title: Evaluation
description: The pnp-core algorithm — trigger set, abstention and speakers, collation, the backstop — and how the bridge carries a snapshot in and a verdict plus applied effects out.
---

Evaluation is `pnp_core::eval::evaluate(forest, snapshot, ctx)`: pure,
allocation-fallible, and the same code under cargo and in the kernel.
Its steps are the ratified design's six, in order.

## 1. Matching

A rule matches iff it is enabled and every one of its conditions holds
against the snapshot. Conditions are a conjunction; a value written as a
list is a disjunction *within* that one field. A disabled rule never
matches, so its subtree is unreachable.

Conditions are evaluated in the order ingestion stored them, which puts
live-time conditions (`Time.*`) **last**, and the conjunction stops at
the first false one. Every live-time condition actually reached — true
or false — is *consulted*, and `Rule::matches_traced()` records into a
`MatchTrace` the moment it would next flip (`Condition::next_flip()`):
for hour, minute, second and day-of-week, the value sequence is scanned
one cycle ahead with the condition's own operator, so `Time.Hour.Equal
9-17` at 10:30 flips at 18:00 and `Time.Hour.LessThan 24` never does;
day-of-month, month and year answer "next midnight", since exact flips
need calendar arithmetic nobody has asked for. A false condition is
consulted too: a higher-priority rule that missed only on the clock may
match later. A rule whose address or port conditions fail first never
consults its clock and contributes nothing. The earliest consulted flip
is the evaluation's `expires_at` — the Flow layer's sentence expiry
(§6.8); the per-packet layers compute it and ignore it.

## 2. The trigger set

The walk descends each tree from its root. A node **triggers** iff it
matches and none of its children match: a matching child shadows its
parent. Shadowing exists only within a lineage — two trees never shadow
each other, and their order in the forest carries no meaning. The walk
returns "matched" to the parent so the parent knows it was shadowed.

## 3. Resolving a triggered rule

Every triggered rule's action list is resolved once. Verdict actions fold
to the strictest listed; `TAG` and `COUNT` push effects; `REPORT` folds
to the highest level listed and pushes one effect if that level clears
`CurrentReportingLevel` (one report per rule per evaluation); `PROMPT`
pushes a prompt-issued effect and, with no handler transport in this
release, resolves its fallback in place (nesting bounded by
`MAX_PROMPT_CHAIN`, 4). Side effects always execute — they are pushed
before anyone knows whether the rule's verdict will win.

## 4. Abstention

A triggered rule that yields no verdict abstains. The walk then goes up
the rule's own parentage — the chain it descended by — to the nearest
ancestor whose actions contain a *direct* verdict (a top-level `PASS`,
`DROP` or `REJECT`; a verdict inside a `PROMPT` fallback does not count),
and that ancestor **speaks for the region**: its full action list
resolves, once. A speaker reached by several abstaining descendants in
one evaluation executes only the first time (`spoken` tracks resolved
speakers by identity). Intermediate abstaining ancestors execute
nothing. If no ancestor bears a verdict, the branch contributes nothing
and other trees or the backstop answer.

The attribution of a speaker's verdict is the speaker's path, not the
abstaining descendant's.

## 5. Collation

Every yielded verdict is a candidate `(verdict, priority, path)`. The
winner has the highest priority; at equal priority the strictest
verdict: `DROP` (3) > `REJECT(Refused)` (2) > `REJECT(Prohibited)` (1) >
`PASS` (0). The two reject ranks are a deterministic tie-break — the
quieter story wins — that exists only because candidate order is
meaningless. Priority is the rule's *effective* priority, resolved at
ingestion: a rule's own `Priority` value, else its parent's, else 0.

## 6. The backstop

No candidate at all: the verdict is `DROP`, attributed to `backstop`,
and the evaluation is flagged so the event can say so. The backstop is
compiled in and un-deletable; every permissive statement in a policy is
therefore a visible rule.

## The evaluation as data

`Evaluation` carries the winning verdict, its attribution, the backstop
flag, every effect to apply, every candidate (winners and losers alike)
for observability, and `expires_at`. Effects reference their stores by
name *and* hash: `Effect::Tag { hash, op }`, `Effect::Count { hash,
amount }` with the amount already resolved (`Length` becomes the packet
length, or 0 when the packet has none), `Effect::Report { rule, level }`,
`Effect::PromptIssued { rule, handler }`.

## The bridge

`pnp_rust_evaluate(forest, snap, layer, reporting_level, out)` is what
`policy.c` calls under `rcu_read_lock()`. It:

1. lifts the C snapshot (§6.3) and resolves the forest's machinery facts
   through the stores — `peios_pnp_tag_lookup()` for every tag name the
   forest mentions (`Packet` and `Flow` layers; `RawPacket` reads none),
   `peios_pnp_counter_read()` for every view — and gives a `Flow` forest
   its own facts, `Related` and `Start.*`;
2. evaluates with `EvalContext { reporting_level }`;
3. writes the verdict, the reject kind, the backstop flag, the truncated
   attribution and `expires_at` (0 = never) into `struct
   peios_pnp_outcome`;
4. **then** applies the effects — `peios_pnp_tag_apply()`,
   `peios_pnp_counter_add()`, `peios_pnp_report_emit()` with the verdict
   it just computed — counting each species into the outcome.

Ordering 4 after 2 is what the snapshot-immutability law requires: a
`COUNT` is applied after this packet's own view reads, so a rule cannot
trip its own threshold, and a `REPORT` can name the verdict. Every
allocation in 1–2 is `GFP_ATOMIC` (`pnp-core`'s `pkm_alloc` in kernel
mode); a failure returns `-ENOMEM` and the hook fails closed (§6.2). The
store calls never sleep.
