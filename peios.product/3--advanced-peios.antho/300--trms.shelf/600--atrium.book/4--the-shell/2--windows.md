---
title: Windows
description: A flat window list with one focus — numbering, minimise, the title bar, and one sidebar entry per window.
---

The session keeps a flat list of windows and at most one focused
window. Each window belongs to an application, has a session-minted
id and a title, and is either visible or minimised.

**Opening.** `launch` names an app. If the app already has a window,
the most recent one is focused instead — one window per application is
the default, and a second is the deliberate ask `launch { new: true }`
(the context menu's "Open in new window"). Windows of one application
are numbered by the session as they multiply: "Terminal",
"Terminal 2".

**Focus.** Focusing a minimised window restores it first
(`window.restored`, then `focus`). Closing or minimising the focused
window passes focus to the most recently opened still-visible window,
or to none — and a tab showing no focused window shows the Toolbox.

**Minimise** is session state like everything else: the frame stays
loaded in every tab, hidden; the sidebar entry dims. Whether a given
tab is looking at its windows or at the Toolbox is the one piece of
state that is deliberately per-tab.

**Chrome.** The focused window sits under a bar with its
application's glyph and title on the left and two lights on the
right: yellow minimises, red closes. Each open window has its own
sidebar entry — running dot, dimmed when minimised, highlighted when
focused; middle-click closes it. Pinned applications without windows
show a single launcher entry.

An application's frame is served from the session host
(`/apps/<id>/…`), created hidden, and revealed by the SDK handshake or
by a 1.2-second grace for pages that never load the SDK (§5.3).
