---
title: Preparing a Monthly OS Release
type: how-to
description: Selecting and qualifying component releases for a monthly OS
  baseline.
---

A monthly OS release combines qualified component releases into one Peios
baseline. Prepare each monthly on a temporary `monthly/<os-version>` branch
created from `main`:

1. Select the component releases to include, respecting their dependencies.
2. Merge their exact release tags into the monthly branch using ordinary Git
   merges. Do not merge moving development tips or unfinished component work.
   Components without an update retain their existing versions.
3. Update the Peios edition package and release lock to identify the selected
   package artifacts, source revisions, and dependency closure. Include the
   exact kernel revision from the separate kernel repository.
4. Build and qualify the assembled OS. Passing component tests alone does not
   qualify the selected combination.
5. Advance `main` to the qualified monthly result and tag it
   `peios/v<os-version>`. Publish the qualified artifacts. If the candidate
   changes during integration, repeat the affected validation before
   promotion.
6. Merge the resulting `main` into active forward-development component
   branches and validate those integrations. This gives them the new monthly
   baseline while retaining their ongoing work.

Keep `main` at the previous qualified monthly until the candidate is ready.
Preserve merge ancestry when consolidating releases and feeding the baseline
back into development; do not squash or rebase those integrations.

The monthly source tree should agree with the selected component releases. If
integration requires a change to already released component code, make a
corrected component release and update the selection. Do not silently ship
modified component code under an existing version.

Use temporary integration branches to test prospective combinations throughout
the month. Finding incompatibilities should not wait until the release cut.
