---
title: Reply Validation
description: How resolvd decides a reply belongs to its transaction, what happens to one that does not, and what it takes from one that does — outcome, records, case and lifetime.
---

## Matching

A reply is matched against the transaction it arrived for. It matches
when all of these hold:

1. it decodes as a DNS message;
2. its ID equals the transaction's;
3. its `QR` bit is set;
4. it has exactly one question;
5. that question's type and class equal those sent;
6. that question's name is byte-for-byte identical to the name sent,
   case pattern included. [*engine-reply.match-conditions]

A reply that fails any of these is ignored: the transaction is not ended
by it, nothing is counted, and the server is not demoted for it. [*engine-reply.non-matching-reply-ignored]

### A non-matching datagram on UDP

A UDP transaction's socket is closed as soon as one datagram has been
read from it, before the datagram is matched. A datagram that does not
match therefore leaves its transaction with no socket: no later
datagram, including the server's real reply, can reach it. The
transaction then ends at its two-second deadline as a timeout, which
fails the attempt and demotes the server (§4.6). [*engine-reply.non-matching-udp-datagram-becomes-timeout]

The same holds for a datagram that does not decode, or that was longer
than the 4 096-byte read buffer and so arrived cut short. [*engine-reply.undecodable-or-cut-short-datagram-becomes-timeout]

A TCP transaction's connection is likewise closed after its first
message, so a non-matching TCP reply also ends in a timeout. [*engine-reply.non-matching-tcp-reply-becomes-timeout]

## A matching reply

A matching reply adds one to `upstream_answered` and ends the
transaction. Then:

| Reply | Result |
|---|---|
| UDP, `TC` set | TCP retry to the same server (§4.7) |
| Response code `NOERROR` | `found` [*engine-reply.noerror-is-found] |
| Response code `NXDOMAIN` | `notfound` [*engine-reply.nxdomain-is-notfound] |
| Any other response code | The attempt fails (§4.6) |

The response code is the header's four bits combined with the extended
bits of an `OPT` record in the reply, so an extended code is never
mistaken for `NOERROR` or `NXDOMAIN`. [*engine-reply.extended-rcode-combined]

A `NOERROR` or `NXDOMAIN` reply removes the server's demotion (§4.6).

## What is taken from it

**Records.** The answer section's records of class `IN`, in the order
the server sent them. [*engine-reply.answer-records-of-class-in] For `NXDOMAIN` none are taken, even if the server
sent some. [*engine-reply.nxdomain-records-discarded] Records are not checked against the question: an `IN` record
at any name, of any type, in the answer section is returned to the
client and cached with the answer. [*engine-reply.records-not-checked-against-question] The authority and additional
sections are not returned. [*engine-reply.authority-and-additional-not-returned]

**Case.** A record whose owner name equals the candidate,
case-insensitively, is given the candidate's case — the case of the
question as asked, not the randomised case sent. Other records keep the
case the server used. [*engine-reply.candidate-case-restored]

**Lifetime.** The cache lifetime of §4.5, computed from the answer
records or from the authority section's `SOA`.

**Flags.** The server's `AA`, `AD`, `RA` and `CD` bits are not used and
are not carried into any answer. [*engine-reply.upstream-flags-not-carried] A `NOERROR` reply with an empty answer
section — including a referral from a server that does not recurse — is
`found` with no records. [*engine-reply.empty-noerror-is-nodata]

A `notfound` with further candidates moves to the next one (§4.3);
everything else answers the question.
