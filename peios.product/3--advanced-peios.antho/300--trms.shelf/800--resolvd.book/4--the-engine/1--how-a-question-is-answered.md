---
title: How a Question Is Answered
description: The path every question takes through the engine, in order — parsing, synthetic names, candidates, routing, the cache, the network — and what each way out reports as its source.
---

Every door ends here. The native socket's `resolve`, `lookup` and
`reverse`, and every stub query, become one or more tasks, and each task
takes the same path.

## The path

1. **Parse.** The name is parsed from presentation form. A trailing dot
   makes no difference. Escapes are not interpreted; a label is the
   bytes between dots. A name with an empty label, a label over 63
   bytes, or more than 255 bytes on the wire does not parse, and the
   task is answered `notfound` at once. [*engine-flow.unparseable-name-is-notfound]
2. **Synthetic names.** The name as asked is checked against the
   synthetic names (§4.2). A match answers the task. [*engine-flow.synthetic-check-first]
3. **Candidates.** The name becomes its list of candidates (§4.3). An
   empty list — a single label with no applicable search domain —
   answers the task `notfound`. [*engine-flow.no-candidates-is-notfound]
4. **Each candidate in turn:**
   1. it is routed to one scope (§4.4); when no scope can take it, the
      task is answered `unavailable`; [*engine-flow.unroutable-candidate-is-unavailable]
   2. unless the request asked to bypass the cache, the cache is
      consulted under that scope (§4.5);
   3. otherwise it is sent upstream (§4.6 to §4.8).

   A `notfound` for a candidate — from the cache or from a server —
   moves to the next candidate when there is one. Any other result
   answers the task. [*engine-flow.notfound-moves-to-next-candidate]
5. **No candidates left.** When every candidate was `notfound`, the task
   is answered `notfound`. [*engine-flow.all-candidates-notfound-is-notfound]

Each candidate is routed separately, so the expansions of one single
label can go to different scopes. [*engine-flow.each-candidate-routed-separately] Each has its own attempt budget
(§4.6).

## What each way out reports

| Ends at | Outcome | `source` | `server` | `interface` | `rcode` |
|---|---|---|---|---|---|
| Name does not parse | `notfound` | `local` | nil | nil | 0 [*engine-flow.report-unparseable] |
| Synthetic name | per §4.2 | `synthetic` or `hosts` | nil | nil | 0 [*engine-flow.report-synthetic] |
| No candidates | `notfound` | `local` | nil | nil | 0 [*engine-flow.report-no-candidates] |
| No scope can take the candidate | `unavailable` | `local` | nil | nil | 0 [*engine-flow.report-unroutable] |
| Cache hit | as cached | `cache` | the server that answered | the scope's interface | the cached response code [*engine-flow.report-cache-hit] |
| A server's reply | `found` or `notfound` | `dns` | the server | the scope's interface | the server's response code [*engine-flow.report-server-reply] |
| Every candidate `notfound` | `notfound` | `local` | nil | nil | 0 [*engine-flow.report-all-candidates-notfound] |
| Attempts exhausted | `unavailable` | `local` | nil | the scope's interface | 0 [*engine-flow.report-attempts-exhausted] |
| No servers left in the scope | `unavailable` | `local` | nil | nil | 0 [*engine-flow.report-scope-without-servers] |
| In-flight ceiling reached | `unavailable` | `local` | nil | nil | 0 [*engine-flow.report-in-flight-ceiling] |

Two rows are worth noticing. A single label whose every expansion came
back `NXDOMAIN` from a server reports `local`, not `dns`, because the
last decision — that nothing is left to try — was resolvd's. And
`interface` is nil for every answer from the fallback scope, which has
no interface. [*engine-flow.fallback-scope-has-no-interface]

`validation` is `unvalidated` in every case: resolvd performs no DNSSEC
validation (PSPU §6.6). [*engine-flow.validation-always-unvalidated]

## What an answer carries

An answer's records are the answer-section records of the reply that
decided it, after the filtering of §4.8, or the synthetic records of
§4.2. The engine also carries the candidate the answer was found at; the
stub door uses it to add a `CNAME` (§6.2) and `lookup` uses it as the
start of its CNAME chase (§4.9).

## Nothing is cancelled

A question whose asker has gone — a native client that closed its
connection, a stub TCP client that hung up — is not abandoned. Its
transactions run to completion, its reply is cached, and its answer is
discarded when it cannot be delivered. [*engine-flow.departed-asker-not-cancelled]
