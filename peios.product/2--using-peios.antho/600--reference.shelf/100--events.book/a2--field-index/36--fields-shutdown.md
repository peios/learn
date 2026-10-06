---
title: "shutdown.*"
description: "Every field the evman catalogue defines under shutdown: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `shutdown`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="shutdown.finalization-state"></a>`shutdown.finalization-state`

- **Type:** `str.enum`
- **Values:** `waiting-for-services` · `ready` · `failed` · `completed`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `peinit.evman`

How far the system shutdown had got when the event was written.
`waiting-for-services` means services were still being stopped; `ready`
means they had stopped and the final action had not yet run; `failed`
means finalisation itself went wrong; `completed` means it finished.

**Carried by:**

- [`peinit.critical-service.failed`](~peios/events/peinit/peinit-critical-service-failed)

*Generated from `peinit.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
