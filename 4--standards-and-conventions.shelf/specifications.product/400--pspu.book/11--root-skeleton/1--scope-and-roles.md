---
title: Scope and Roles
description: The file that says what a root needs outside /usr, which no package can ship, and the parties that write and apply it.
---

This chapter defines the **root skeleton file**: a list of the directories
and symbolic links a root needs outside `/usr`, with a security descriptor
for any directory that needs one.

A package installs only under `/usr` (§5.14). A root still needs `/var`,
`/lcl`, `/tmp` and the other directories outside `/usr` before its first
program runs. It also needs `/lib64`, the link through which the x86-64
psABI finds the dynamic loader. Nothing that runs in the root can make
these, because the loader itself needs one of them. Whatever builds the
root makes them, from the skeleton file the root's own `/usr` holds.

## Roles

**The provider** is the package that ships the skeleton file in its
payload, as an ordinary file under `/usr`. On Mainline this is
`dev.peios.fsbase`, and `dev.peios.fsbase-irf` for an initramfs.

**The applier** is whatever builds a root: a live-boot hook that composes
the root at boot, an image builder that composes an initramfs, an
installer, or an upgrade tool. It installs the root's packages, then
reads the skeleton file in that root and makes what it lists.

The provider decides what a root holds outside `/usr`. The applier
decides when to apply the file and against which root, but not what the
file contains. A root's packages, and so its provider, are chosen when
its closure is chosen. Nothing else selects a skeleton.

## What this chapter leaves to others

What goes in `/usr` is the package format's (§5). Policy outside `/usr`
that differs from one image or machine to another, such as registry seeds
or an operator's local files, is not skeleton content. It belongs to the
image, the installer or the operator.

Mounting filesystems at the skeleton's directories is the boot process's
concern. The skeleton makes only the directories and links.
