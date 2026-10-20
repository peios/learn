---
title: What Is Peios
type: concept
description: The ideas that shape Peios, its security model, registry, event system, service manager, and browser desktop, and where to start reading.
related:
  - peios/introduction/how-peios-fits-together
  - peios/introduction/finding-your-way
  - peios/installing-peios/preparing-a-pc
---

Peios is an operating system. Its kernel is based on Linux, and adds its own
security model, configuration store, event system, layered storage, and
network packet policy. Above the kernel, Peios has its own service manager,
sign-in service, and system services, and a desktop that you use from a web
browser. A few ideas run through all of it, and knowing them makes the rest of
this documentation easier to follow.

## One security model for everything

Every decision about who can do what goes through one security model, built
into the kernel:

- Every account, group, and service has a
  [security identifier (SID)](~peios/identity-and-access/security-identifiers)
  that never changes.
- Every running program acts with an
  [access token](~peios/identity-and-access/access-tokens) that says who it
  is, which groups it belongs to, and which
  [privileges](~peios/identity-and-access/privileges) it holds.
- Every protected object, whether a file, a registry key, a service, or a
  process, has a security descriptor that says who can do what to it.

When a program opens a file or changes a setting, the kernel compares the
program's token with the object's security descriptor. No account is exempt
from that check because of its number or name. An administrator has more
access because policy grants it, not because the check is skipped.

## Configuration lives in the registry

Almost all configuration lives in the
[registry](~peios/registry/the-registry): a tree of keys holding typed
values, with a security descriptor on every key. Service definitions, network
profiles, sign-in policy, and desktop preferences are all registry values.

Configuration can come in layers. An installed role and a policy can each set
the same value, and the registry decides which one is in effect without
losing the other. Removing a layer restores what was there before.

## Every event takes one path

The kernel and every service report what they do through one event path.
eventd stores the events, logs, and metrics, and answers queries for them
according to who is asking. Each component documents the events it can emit,
and no component is allowed to emit a field that isn't documented. See
[Interpreting Events](~peios/reading-records/interpreting-events).

## Services are defined and supervised

peinit starts the machine, starts each service in the order its dependencies
require, restarts services that fail, and shuts the machine down. Each
service is defined in the registry, and runs with an identity of its own. See
[Services and Jobs](~peios/services-and-jobs/overview).

## A desktop in your browser

You can use Peios from a desktop in a web browser, at a local console, or
over SSH. The desktop's applications run on the Peios machine, with the
authority of the account you signed in with. See
[Signing In](~peios/signing-in/overview) and
[The Desktop](~peios/desktop-basics/overview).

## Where to start

These pages are good places to begin:

- [How Peios Fits Together](~peios/introduction/how-peios-fits-together) for
  a map of the components and how a machine starts.
- [Preparing a PC](~peios/installing-peios/preparing-a-pc) to install Peios.
- [Finding Your Way](~peios/introduction/finding-your-way) to find the guide
  for a task.
