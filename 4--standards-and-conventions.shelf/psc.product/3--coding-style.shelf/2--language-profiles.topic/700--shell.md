---
title: Shell
type: reference
description: Peios coding conventions for Shell.
---

Keep shell focused on connecting existing commands. Move substantial parsing
or application logic to a more suitable language, considering complexity and
the available runtime rather than imposing a hard script-length cutoff.

Make the intended interpreter explicit and use syntax supported by that
interpreter. Apply the error and cleanup rules to command exit statuses,
pipelines, and temporary resources. Preserve argument boundaries when
expanding values: filenames containing spaces must not silently become several
arguments. Use four-space indentation where shell syntax permits it; syntax
that requires literal tabs retains them.
