---
title: Security Descriptor Overrides
description: A file or directory takes the descriptor its directory gives it unless its entry gives one, the form of one, and the consumer's obligation when it does.
---

A file or directory of a package takes the security descriptor that
inheritance from its directory gives it, unless its entry gives one. An
entry's `descriptor` replaces it.

## Form

A descriptor is a self-relative security descriptor (PCDS) with an owner, a
group and a DACL, written in the manifest as the lowercase hexadecimal of
its bytes. Its bytes are kept as given: two layouts of one descriptor are two
descriptors. A producer MUST check that its parts lie within it; what it
grants is the kernel's to judge.

A symbolic link MUST NOT have one (§5.17). A directory with one is listed in
the manifest even if it has contents (§5.16).

## The consumer's obligation

A consumer that stores a file or directory with a descriptor MUST give it
that descriptor before anything else can reach it: on Peios, as it creates
it. A file with a descriptor is stored as a blob of its own that carries it
(§5.12), so every hard link to it carries it too.

Where the system won't let the consumer give a descriptor, as on a host that
isn't Peios, it MAY leave it out, and MUST then say how many files and
directories lack theirs. The manifest still records them, and a file stored
without its descriptor MUST NOT be linked into a tree on Peios as if it had
it.
