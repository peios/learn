---
title: What an Application Is
description: One contract on two axes — where the UI comes from, and what runs behind it — and the four shapes that fall out.
---

An Atrium application is a directory of web files with a manifest. The
contract has two independent axes rather than kinds:

- **Where the UI comes from.** Either the package ships static files
  and the session host serves them (`entry`, the default), or the
  frame points at a URL Atrium does not serve — an application that is
  its own web server, or someone else's.
- **What runs behind it.** Nothing; commands the session runs on
  request (`exec`, §5.5); a terminal (`pty`, §5.5); or, in a later
  version, a long-running backend process.

The useful shapes fall out of the grid: a pure page (About), a
*wrapper app* — static UI whose buttons run allowlisted commands, most
of the Toolbox's natural contents — a terminal, and an embedded
external web application.

Two properties hold across all of them:

- **Everything an application does on the machine happens as the
  user**, inside the session host's process tree and the session job's
  cgroup. The manifest's capabilities narrow what an application may
  ask the session to do; they never widen who it is.
- **An application that loads the SDK is a citizen; one that does not
  still works.** The SDK is how a frame gets the handshake, the theme,
  requests and shortcuts. A plain page without it is shown after a
  grace period and swallows global chords while focused — degraded,
  deliberately, rather than broken.
