---
title: Component Releases
type: reference
description: Qualifying component releases, immutable tags, and starting the
  next version.
---

Stabilize a component on its version branch. Release candidates can be tagged
`<component>/v<version>-rc.1`, `-rc.2`, and so on. Tag the qualified final
release as `<component>/v<version>`.

Published candidate and final tags are immutable. Further corrections receive
a new candidate or version; an existing tag must not be moved to different
code. The release records the source revision and declared build inputs used
to produce its package artifacts.

After release, start the next version branch from the final tag. The release
tag remains the selection point for monthly integration, even when subsequent
work has advanced a branch.
