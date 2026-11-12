---
title: Terminology
description: Terms this chapter defines for itself — root, skeleton file, provider, applier, entry.
---

**Root.** A directory tree that a system, or an initramfs, runs with as
its `/`. Paths in a skeleton file are relative to it. §11.1

**Skeleton file.** The file at `/usr/share/skeleton` in a root, which
lists what that root needs outside `/usr`. §11.3

**Provider.** The package whose payload holds a root's skeleton file.
§11.1

**Applier.** The program that builds a root and applies its skeleton
file to it. §11.1

**Entry.** One line of a skeleton file that names a directory or a
symbolic link. §11.3

**Descriptor.** A security descriptor (PCDS 5), written in SDDL, that a
directory entry gives for the directory it names. §11.3
