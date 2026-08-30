---
title: Overview
description: Atrium is the Peios web UI — a browser-delivered interactive session. The decisions that would not be guessed from the name.
---

**Atrium** is the Peios web UI. A browser pointed at a Peios machine
gets a login page; a successful logon gets a desktop — windows, apps, a
terminal — served by that machine and running on it. Atrium is not a
management panel over the system; the browser tab *is* the user's
session.

Four decisions shape everything else in this manual:

- **The browser is a renderer.** All session state — which windows
  exist, which is focused, the chord table — lives on the machine, in
  the user's session host. Every connected browser tab holds a mirror
  of that state and asks for changes; no tab owns anything. Two tabs,
  or a laptop and a phone, are two views of one desktop.
- **The shell is thin; applications are the product.** The shell owns
  login, windows, focus, keybinds and the launcher, and nothing else.
  Everything a user opens is an application: a directory of web files
  with a manifest, drawn in an iframe, talking through one SDK
  (chapter 5).
- **Privilege is split across three processes.** The one privileged
  process holds no network socket and parses no HTTP; the process that
  faces the network runs with every privilege deleted; the process
  that does the user's work is the user (chapter 2).
- **Atrium does not create user processes.** Session hosts are
  submitted to peinit as jobs, with the logon token as the job
  identity — peinit is their parent, supervisor and record-keeper
  (§3.2).

Atrium listens on port 8080, unencrypted, and every browser-facing
door is one HTTP origin. Transport security and per-application
origins are not provided in this version.
