---
title: Changes Spanning Components
type: reference
description: Coordinating component changes and testing explicit dependency
  combinations.
---

A component branch might need a change from another component. Merging that
component's development branch also incorporates its history, potentially
including work that is not ready for release.

Agree the integration plan before doing this. Either coordinate the affected
component releases as a group, or keep their development branches separate and
test the proposed combination on a temporary integration branch with explicit
dependency inputs. A component release must not accidentally carry unrelated,
unfinished changes into the monthly.

Builds must use declared dependencies. An unreleased sibling component must
not be substituted merely because it happens to be present in the checkout.
