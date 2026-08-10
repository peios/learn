---
title: Security policy
type: concept
description: How to report a security vulnerability in Peios privately, what to expect after you report, and what is in scope.
related:
  - project/policies/licensing-and-source
---

Peios is an operating system, and its security model is one of its central features. If you believe you have found a vulnerability in any part of it, report it privately so a fix can land before the details are public.

## How to report

Email **security@peios.org**. Do not open a public issue, and do not include vulnerability details in commits, pull requests, or public discussion before a fix is released.

A useful report includes:

- The component and version (or commit) you tested — for example the kernel (PKM/KACS), `peipkg`, `peinit`, `loregd`, or an image built with a stated release.
- What you observed, and why you believe it crosses a security boundary. On Peios that usually means the KACS access-control model, the signing and verification chain, or the package and boot pipeline.
- Steps or code to reproduce it. A provium test is ideal but plain shell steps are welcome.

The machine-readable form of this policy lives at `/.well-known/security.txt` on this site, per RFC 9116.

## What to expect

Peios is developed by a small team, so the process is deliberately simple:

- You should normally receive an acknowledgement within a week.
- Reports are handled on a coordinated-disclosure basis: the details stay private until a fix is available, and you will be told when that happens. If you need a firm disclosure date, propose one in your report.
- Fixes ship in the next release, and the release notes credit reporters who want to be credited.
- There is no bug-bounty programme.

## Scope

In scope: every first-party Peios component — the PKM kernel tree, the userspace daemons and libraries, the packaging and image pipeline (`pekit`, `peipkg`, `peiso`), and the published images and packages themselves.

Vulnerabilities in third-party upstream software that Peios packages should go to the upstream project first; report them here as well when Peios's packaging or configuration makes the impact worse.

## Where to go next

- [Licensing and source availability](~project/policies/licensing-and-source) — the terms Peios ships under and how to get its source.
