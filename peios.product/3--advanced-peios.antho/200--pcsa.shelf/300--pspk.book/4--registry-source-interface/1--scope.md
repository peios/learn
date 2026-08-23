---
title: Scope and Roles
description: The RSI contract between the kernel's registry subsystem and the userspace sources that store data for it — and what a source is not.
---

This chapter specifies the **Registry Source Interface (RSI)**: the
protocol between the Peios kernel's registry subsystem and the
userspace processes that store registry data for it.

Two roles participate.

The **kernel** is LCS, the Layered Configuration Subsystem. It owns the
registry namespace, the layer model, access control, watches and
transactions, and it holds no storage of its own. There is one kernel.

The **source** is a userspace process that stores the data for one or
more hives and answers the kernel's requests about it. The source role
is publicly implementable: any process holding the required privilege
MAY register as a source, and the kernel is source-agnostic. A
conforming source is the subject of the requirements in this chapter.

The kernel is the party asking. A source is authoritative for the bytes
it returns and for nothing else.

This chapter covers:

- the character device, how a source attaches to it and is recognised,
  and the source slot lifecycle
- the framing and encoding of requests and responses, and the rules
  under which each may be extended
- every operation the kernel issues, its request payload, its response
  payload, and its meaning
- the status vocabulary a source answers with
- what the kernel validates for itself rather than believing
- the obligations a conforming source MUST satisfy

This chapter does not cover:

- The registry data model — hives, keys, path entries, values, layers,
  tombstones, resolution — which is described in the Peios Kernel TRM.
  A source does not need it.
- The system-call and ioctl surface the registry offers to ordinary
  programs, which is that subsystem's own documentation.
- The registry backup format, which is specified in its own chapter.
- How a source stores its data, serves concurrent requests, or computes
  its answers.

## What a source is not

A source stores and returns. It MUST NOT resolve layers, filter results
by visibility, evaluate a Security Descriptor, interpret a path beyond
the parent and child names it is given, or dispatch a notification.
Every such decision belongs to the kernel, and a source that made one
would be making it with less information than the kernel has.

A source never learns the identity of the process on whose behalf a
request was issued. Requests carry no caller identity, and there is no
mechanism by which a source could obtain one.

## What the kernel establishes for itself

The kernel validates that every response is structurally well-formed,
that names are valid, that Security Descriptors parse and satisfy the
mask rules, that sequence numbers cannot be from the future, and that
metadata blocks cover exactly the GUIDs they should. §4.5 lists these.

It cannot validate meaning. A source is inside the trusted computing
base precisely because the kernel has no independent copy of what a
source returns: a Security Descriptor granting everyone full access to
a sensitive key is a valid Security Descriptor, and the kernel will
enforce it.

A source is trusted with the correctness of the registry's access
control for the hives it backs. That is the whole trust model, and it
is why attaching requires the highest privilege the system has.
