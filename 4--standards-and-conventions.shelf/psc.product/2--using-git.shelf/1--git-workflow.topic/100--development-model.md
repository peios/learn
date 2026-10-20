---
title: Development Model
type: concept
description: The trial component-led development model and the role of
  Panorama.
---

Peios is trialing a component-led development model. Components develop and
release independently; monthly OS releases consolidate selected component
releases into a shared baseline. The model remains subject to revision if
experience shows that its integration or maintenance costs outweigh its
benefits.

Panorama is a development workspace for the OS. Its components remain
separate, independently versioned packages. A Git branch or tag always
identifies a whole repository state; a component name describes its purpose,
not a restriction Git enforces on the files or history it contains.
