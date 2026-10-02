---
title: Scope and Roles
description: The interface by which a program has a person edit the Security Descriptor of an object it holds, in an editor that is a program of its own and never touches the object.
---

This chapter defines the **editing channel**: the interface by which a
program has a person edit the Security Descriptor of an object the
program holds, in a dialog drawn by another program, the **editor**.

The object may be of any kind that has a Security Descriptor — a file,
a registry key, a service. The editor knows none of them. What it is
told is what a person needs in order to edit the descriptor: what the
object is called, what kind of thing it is, what its rights are called,
and the descriptor itself. What it answers with is a descriptor.

## Roles

**The requester** is the program whose object it is. It starts the
editor, reads the object's descriptor, tells the editor about it, and
applies each descriptor the editor sends back. It holds the object, and
whatever right changing the descriptor takes, throughout.

**The editor** draws the descriptor for a person to change, on the
desktop the requester is on, and sends back what they apply. It holds
no handle to the object and needs no right over it. It changes nothing
itself.

The split is deliberate. The party that can change the object is the
one that already holds it, and it applies exactly what it is sent, so
an editor serves every kind of object without ever being trusted with
one. A requester gains a full editor without containing one.

> [!NOTE]
> The arrangement is the one Windows' security editor uses, where the
> caller implements the object's side (`ISecurityInformation`: the
> descriptor, the rights' names, applying) and the editor draws. Here
> the editor is a separate process rather than a library, so that it
> serves a requester in any language, and a fault in it is its own.

## What this chapter leaves to others

How the editor draws its dialog, and on which desktop, is the editor's
own design and that desktop's. On a GXWI desktop the editor is an app
like any other, found by the environment it inherits from the
requester.

The layout of a Security Descriptor, of the access masks it carries
and of its entries is PCDS §5's. This chapter carries descriptors and
says nothing about their contents beyond which components are applied.

How a requester reads and applies a descriptor is its own concern, and
depends on the kind of object. A requester SHOULD apply through the
same handle it read through, so that what is applied reaches the object
that was shown, wherever it has gone in the meantime.
