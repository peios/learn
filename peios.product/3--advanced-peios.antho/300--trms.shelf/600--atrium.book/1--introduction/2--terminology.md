---
title: Terminology
description: The three session concepts — browser, interactive, logon — and the smaller vocabulary of shell, mirror, window and application.
---

Three different things are reasonably called "a session", and Atrium
keeps them distinct:

| Term | What it is | Owned by |
|---|---|---|
| **Logon session** | The kernel's unit of identity: created by authd per successful logon conversation, identified by the token's LUID, spanning every process carrying that token | KACS / authd |
| **Interactive session** | One running desktop: the `atrium-session` process and its state — windows, focus, applications, terminals | Atrium |
| **Browser session** | One browser's binding to an interactive session: a cookie | atrium-server |

They are one-to-one-to-one today — one login produces one logon
session, one interactive session and one cookie — but the concepts
diverge as features arrive: a second device attaching to an existing
desktop adds a browser session without a logon; an unlock re-runs a
logon conversation without touching the interactive session.

The rest of the vocabulary:

- **Shell** — the chrome a logged-in browser renders: topbar, sidebar,
  Toolbox, window frames. One page, served by the session host.
- **Mirror** — one connected shell's copy of the session state, kept
  current over a websocket (§4.1).
- **Window** — one open application instance: an entry in the session's
  window list, and one iframe in every mirror.
- **Application (app)** — an installed directory under
  `/usr/share/atrium/apps/<id>/` with a manifest; what the Toolbox
  launches (chapter 5).
- **Session host** — the `atrium-session` process of one interactive
  session.
- **The bus** — the postMessage path between an application's frame,
  the shell, and the session host (§5.4).
