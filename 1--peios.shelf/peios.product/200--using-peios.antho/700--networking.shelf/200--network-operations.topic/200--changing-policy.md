---
title: Changing Network Policy
type: how-to
description: Validate interface and firewall decisions independently and retain a recovery path for live changes.
---

Peios Network Policy uses registry rule trees under
`Machine\System\Network`. netd applies `Interface` rules; the kernel's NTFE
applies `RawPacket`, `Packet`, and `Flow` rules. The two consumers validate
their own layers independently.

## Inspect, change, and verify

1. Establish the intended connection and listener. An allow rule does not
   start a listener or grant its port reservation.
2. Record `net status` and, with kernel-device access, `net policy`.
   Distinguish a stored rule from the accepted generation. A refused update
   keeps the previous accepted configuration active.
3. Preview the smallest change. Network Manager offers configuration tools,
   but its labeled example activity data is not evidence of a real flow.
4. Preserve old values and local recovery access before changing a remote
   connection's path. Rule and network-label changes can affect established
   connections on their next packet.
5. Write the intended policy, then run `net policy wait` and `net policy`.
   Check `net status` separately for interface/profile acceptance and test
   the actual service connection.

Read [Changing Network Settings](~peios/system-tools/changing-network-settings)
for exactly which desktop changes have a keep/undo countdown. Direct
registry edits and the development PNP viewer do not provide that safeguard.
A timeout or refusal from the acceptance check needs investigation.

## Choose the evaluation layer

Use `Flow` for most connection and service policy. `Packet` evaluates
per-packet conditions, including traffic without a tracked flow. `RawPacket`
works at wire-side seats; its available facts differ. An allow in one layer
does not override a refusal in another. `Interface` selects a profile,
leaves an interface alone, or keeps it down.

Rules have conditions, actions, and inherited priority. A matching child is
an exception within its parent tree; separate trees still compete. Highest
priority wins, then the stricter verdict. An effect such as counting does
not grant access. The [shared authoring
reference](~peios/network-operations/rule-authoring) defines the vocabulary;
the kernel's [evaluation
reference](~kernel/internals/ntfe/evaluation) defines execution.

## Check a changing flow

A flow's cached verdict is its sentence. Its direction follows the originator,
including replies. Policy or network-context changes cause reevaluation on
the next packet. Consulted `Time.*` conditions can also expire a sentence;
`Start.*` describes connection start and stays fixed. Loopback has two local
endpoints and must pass both judgments.

Use native `Local.*` facts for a local program or service. They derive from
socket identity stamps, not a claimed process name or a projected Unix UID.
Missing identity can mean a kernel endpoint, shared receivers, or no listener.
The [identity reference](~kernel/internals/ntfe/the-identity-facts) explains
when each fact exists.

`DROP` is silent. `REJECT(Refused)` resembles an unavailable listener;
`REJECT(Prohibited)` reports policy refusal. Some packets cannot receive a
refusal, so the engine counts a degraded drop. A newly rejected established
TCP flow can be torn down at both ends. Kernel-generated refusal packets
have a specific bypass; ordinary traffic does not inherit it.

## Interpret observations

Generation zero is permissive before policy ingestion. An accepted empty
packet forest has a drop backstop; an unmatched interface is ignored.
Record which state the machine is in before interpreting a missing rule.

A cached sentence produces no fresh evaluation event for each packet.
Missing events do not prove delivery, and captured frames can precede a
later drop. Check surfaced capture loss, verdict overwrite, and refusal
counters alongside flow attribution.
