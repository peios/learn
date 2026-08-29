---
title: Terminology
description: The terms this chapter uses — name, question, record, scope, outcome, door — and the sense in which each is used.
---

**Name.** A DNS domain name: a sequence of labels. Names compare
case-insensitively (RFC 4343). A **single-label** name has one label;
every other name is **multi-label**. The distinction governs search
expansion (§6.7).

**Question.** A name and a record type (and class, always `IN`). What a
client asks, and the unit the cache is keyed on.

**Record.** A resource record: name, type, TTL, and data. The protocol
is **record-level**: an answer is records, not addresses shaped for a
particular libc structure. `lookup` (§6.5) is the one convenience that
returns addresses, because that is the question every `getaddrinfo`
asks.

**Scope.** What one interface contributes to resolution: its servers,
its search domains, its addresses, whether it claims unmatched names,
whether it is exclusive. Scopes come from the network manager (§6.9).
The **fallback scope** is the registry's server list, used only when no
interface contributes servers.

**Route.** The scope a question goes to. Every question goes to exactly
one scope (§6.7).

**Outcome.** How a question ended: `found`, `notfound`, or
`unavailable` (§6.6). The three are not interchangeable and no door may
collapse two into one.

**Source.** Where an answer came from: `synthetic`, `hosts`, `cache`,
`dns`, or `local` (an answer that needed no lookup at all).

**Door.** A way in: the native socket, the stub listener, or the NSS
shim. The doors differ in who can use them and what they can carry; the
function behind them does not (§6.3).

**Synthetic answer.** An answer the resolver gives from what it knows
about the machine, before any network: loopback, the machine's own name,
static names from the registry, and their reverses.

**Control object.** The resolver's access-control object, a security
descriptor against which every native request is checked (§6.4).

**Stub door.** DNS itself, on the loopback address `127.0.0.53`, for
programs that speak DNS directly (§6.8).
