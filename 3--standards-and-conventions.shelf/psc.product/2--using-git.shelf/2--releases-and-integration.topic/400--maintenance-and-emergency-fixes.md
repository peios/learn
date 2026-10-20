---
title: Maintenance and Emergency Fixes
type: reference
description: Maintaining released versions and carrying fixes into supported
  lines.
---

Create a maintenance version branch from the release being fixed. For example,
create `authd/0.8.1` from `authd/v0.8.0`, apply and qualify the correction,
then tag `authd/v0.8.1`. Do not start an older-line maintenance fix from newer
development.

Carry applicable fixes into forward development and other supported versions,
adapting and testing them as necessary. An urgent fix can land on the older
line first; carrying it forward remains part of the work.

To update an older OS monthly, create a maintenance branch from its
`peios/v<os-version>` tag, integrate the appropriate component fixes, update
its package selection and lock, and qualify a new OS patch release. Do not
merge the latest `main` into older component or OS maintenance branches: that
would import newer development or release content.

Retain published release tags and their referenced source. The duration of
support for older versions is a separate release policy; this branching model
allows maintenance without promising indefinite support.
