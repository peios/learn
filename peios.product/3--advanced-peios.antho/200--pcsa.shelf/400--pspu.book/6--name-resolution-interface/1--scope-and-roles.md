---
title: Scope and Roles
description: What NRI specifies — how programs on a Peios machine resolve names through one resolver, and how the network manager feeds it — and its three roles.
---

This chapter specifies the **Name Resolution Interface (NRI)**: the
protocol by which a program asks the machine's resolver for the records
behind a name, the protocol by which the network manager tells the
resolver what each interface contributes, and the obligations of the
resolver that stands between them.

Three roles participate.

The **resolver** is the one process on a machine that answers names. It
is a *stub* resolver — a DNS client — not a recursive or authoritative
server: it answers synthetically, from the registry, from its cache, or
by forwarding to an upstream server chosen by policy. It listens on a
Unix socket (§6.4) and on the loopback DNS port (§6.8); it never dials
a client. Peios' resolver is `resolvd`; another implementation MAY stand
in its place, and the obligations in §6.11 are what "stand in its place"
means.

A **client** is any process that asks. Most clients never see this
protocol: they call `getaddrinfo`, and the NSS shim (§6.10) speaks it
for them. Peios-native tools, the operator command and the network
manager speak it directly. A client is not trusted by the resolver
beyond what the control object grants it (§6.4).

The **network manager** is the process that knows what each interface
contributes — servers, search domains, addresses, whether it carries the
default route. It publishes that to the resolver over the manager's own
control socket (§6.9); the resolver subscribes. Nothing about the live
network is ever written to the registry to get from one to the other.

This chapter covers:

- the three doors and the one function behind them (§6.3)
- the native channel: socket, framing, access (§6.4)
- the requests and their replies (§6.5)
- what an outcome and a validation state mean (§6.6)
- the resolution model: scopes, routing, expansion, synthetic names,
  the cache (§6.7)
- the stub door (§6.8)
- the network manager channel (§6.9)
- what the hosts shim must and must not do (§6.10)
- conformance, by role (§6.11)
- a message reference and the limits (§6.A1, §6.A2)

What this chapter does not specify: DNSSEC validation and encrypted
transports (reserved; a resolver reports `unvalidated` until it does
them), multicast DNS, and per-caller resolution policy. Each has a
place held for it in the wire format so that adding it is additive.
