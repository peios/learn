---
title: "prompt.*"
description: "Every field the evman catalogue defines under prompt: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `prompt`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="prompt.handler"></a>`prompt.handler`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

The name of the handler a `PROMPT` action addressed. NTFE has no handler
transport yet, so every prompt falls back at once; the handler's name is
the operator's only clue to which integration is missing.

**Carried by:**

No event carries this field yet.

## <a id="prompt.handler-fallback"></a>`prompt.handler-fallback`

- **Type:** `str`
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `ntfe.evman`

What a `PROMPT` fell back to when its handler did not answer: the action
its fallback resolved to, as the rule wrote it. Fallbacks can themselves
be prompts, up to four deep, and this is the action at the end of the
chain.

**Carried by:**

No event carries this field yet.

*Generated from `ntfe.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
