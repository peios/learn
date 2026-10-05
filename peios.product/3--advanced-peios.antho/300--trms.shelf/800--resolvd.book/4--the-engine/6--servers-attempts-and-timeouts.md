---
title: Servers, Attempts and Timeouts
description: Which server each attempt goes to, what counts as a failure, how demotion works, how many attempts a question gets and how long it can take, and the in-flight ceiling.
---

Server order, demotion and the attempt limit are set by PSPU §6.7, and
the contract's mainline values are in PSPU §6.B. resolvd's values are:

| Bound | Value |
|---|---|
| Transaction timeout | 2 s [*engine-servers.transaction-timeout] |
| Attempts per candidate | 3 [*engine-servers.attempts-per-candidate] |
| Demotion period | 30 s [*engine-servers.demotion-period] |
| Upstream transactions in flight | 4 096 [*engine-servers.in-flight-ceiling-value] |

## Choosing the server

For each attempt, the scope's servers — or the fallback servers — are
put in order: the servers not currently demoted, in their configured
order, followed by the demoted ones, in their configured order. [*engine-servers.healthy-first-then-demoted] The
attempt goes to the first server in that order not yet asked for this
candidate. When every server has been asked, it goes to the server at
position *n* mod *count* in that order, where *n* is the number of
attempts already made for the candidate. [*engine-servers.server-choice-rule]

With one server, all three attempts go to it. [*engine-servers.single-server-gets-every-attempt] With two healthy servers
`A` and `B`, the attempts go to `A`, `B`, then whichever of them is
first in the order at that moment — `A` if both have since been
demoted, since demotion keeps configured order within the demoted group.

The order is computed afresh for each attempt, so a server demoted by
the previous attempt is already behind its peers for the next. [*engine-servers.order-recomputed-each-attempt]

Attempts for one candidate are made one at a time; a transaction is
sent only after the previous one for the same candidate has ended. [*engine-servers.attempts-sequential]

## What fails an attempt

Each of the following ends the transaction, adds one to
`upstream_failed`, demotes the server, and moves to the next attempt:

- no matching reply within 2 seconds of the transaction being sent; [*engine-servers.timeout-fails-attempt]
- an error opening, binding, connecting or sending on the transaction's
  socket — an unreachable network is known at once, not after the
  timeout; [*engine-servers.send-error-fails-attempt-at-once]
- an error receiving on a UDP socket, such as the refusal that follows
  an ICMP port-unreachable; [*engine-servers.udp-receive-error-fails-attempt]
- for TCP, a failed connection, an error or hang-up before the query is
  sent, or the connection closing before a whole reply has arrived; [*engine-servers.tcp-failure-fails-attempt]
- a matching reply whose response code is neither `NOERROR` nor
  `NXDOMAIN` — `SERVFAIL`, `REFUSED`, `FORMERR`, `NOTIMP`, and every
  other code, including EDNS extended codes. [*engine-servers.failure-rcodes-fail-attempt]

A reply that does not match the transaction is not itself a failure,
but on UDP it ends the transaction's chance of a reply (§4.8).

## Demotion

Demoting a server marks its address until 30 seconds from now; a
further failure moves that mark forward. [*engine-servers.demotion-marks-address-for-30-seconds] A reply from the server with
response code `NOERROR` or `NXDOMAIN` removes the mark at once. [*engine-servers.good-reply-clears-demotion] The mark
belongs to the address, so a server listed by two scopes is demoted in
both. [*engine-servers.demotion-is-per-address]

A demoted server is still asked, after the healthy ones. [*engine-servers.demoted-servers-still-asked] `status` lists,
for each scope, which of its servers are demoted at that moment (§5.3);
demotion of the fallback servers is not reported. [*engine-servers.fallback-demotion-not-reported]

## The attempt limit

A candidate gets three attempts. When the third fails, the question is
`unavailable` (§4.1), and later candidates are not asked. [*engine-servers.third-failure-is-unavailable]

The limit counts per candidate, not per question: a single label with
*N* candidates can make up to 3*N* attempts. [*engine-servers.limit-is-per-candidate] The TCP retry that follows
a truncated reply (§4.7) is a transaction with its own two-second
deadline but is not an attempt, and does not use up one of the three. [*engine-servers.tcp-retry-not-an-attempt]

Worst cases, from the first transaction to the answer:

| Question | Longest time |
|---|---|
| A multi-label name, every attempt timing out | 6 s |
| The same, with every reply truncated just before its deadline and every TCP retry timing out | 12 s |
| A single label with *N* candidates, every attempt timing out | 6 s on the first; later candidates are reached only after a `notfound` |
| A single label whose first *N* − 1 candidates are `notfound` and whose last times out | (*N* − 1) round trips plus 6 s |

## The in-flight ceiling

When 4 096 transactions are outstanding, a candidate about to make its
first attempt is answered `unavailable` at once, and the `refused`
counter goes up by one. [*engine-servers.in-flight-ceiling-refuses-first-attempts] Later attempts and TCP retries are not checked
against the ceiling. [*engine-servers.retries-not-checked-against-ceiling] Synthetic names and cache hits are answered as
usual whatever the count. [*engine-servers.local-answers-unaffected-by-ceiling]
