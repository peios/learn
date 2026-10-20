---
title: Security Policy
type: concept
description: How to report a security vulnerability in Peios privately, what
  happens after you report it, and what is in scope.
---

If you believe you have found a vulnerability in any part of Peios, report it
privately so that a fix can be released before the details are public.

## How to report

Email **security@peios.org**. Don't open a public issue, and don't put
vulnerability details in commits, pull requests, or public discussion before
a fix is released.

A useful report includes:

- the component and the version or commit you tested, such as the kernel,
  authd, peinit, or loregd, or the release an image was built from;
- what you observed, and why you believe it crosses a security boundary,
  such as the KACS access control model, the signing and verification chain,
  or the boot process;
- the steps or code that reproduce it. A Provium test is ideal, but plain
  shell steps are welcome.

The same policy is available in machine-readable form at
[`/.well-known/security.txt`](https://learn.peios.org/.well-known/security.txt),
as RFC 9116 describes.

## What happens next

Peios is developed by a small team, so the process is simple:

- You should normally receive an acknowledgment within a week.
- Reports are handled by coordinated disclosure: the details stay private
  until a fix is available, and you're told when that happens. If you need a
  firm disclosure date, propose one in your report.
- Fixes ship in the next release, and the release notes credit reporters who
  want to be credited.
- There is no bug bounty program.

## Scope

Every first-party Peios component is in scope: the kernel, the userspace
services and libraries, the tools that build and package Peios, and the
published images and packages.

Report a vulnerability in third-party software that Peios packages to its
upstream project first. Report it here as well when the way Peios packages or
configures the software makes the impact worse.
