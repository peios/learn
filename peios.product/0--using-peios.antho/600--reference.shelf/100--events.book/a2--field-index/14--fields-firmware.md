---
title: "firmware.*"
description: "Every field the evman catalogue defines under firmware: its type, values and meaning, and the events that carry it."
---

Every field the catalogue defines under `firmware`, in path order. Each entry gives the field's definition and, under **Carried by**, every event type that writes it.

## <a id="firmware.policy-mode"></a>`firmware.policy-mode`

- **Type:** `str.enum`
- **Values:** `enforce` · `log`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The firmware signature policy in force. `enforce` refuses a firmware blob
that does not verify at the PeiosTcb tier; `log` loads it anyway and
records the verdict.

**The shipping default is `log`.** On a stock system a failing
`firmware.result` therefore does not mean the blob was refused; read this
field before concluding that a device went without its firmware. The mode
is fixed for the boot and never changes at runtime.

**Carried by:**

No event carries this field yet.

## <a id="firmware.policy-origin"></a>`firmware.policy-origin`

- **Type:** `str.enum`
- **Values:** `compiled-default` · `command-line`
- **Set:** closed
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

Where `firmware.policy-mode` came from for this boot. `compiled-default`
is the kernel build's own setting; `command-line` is a `kacs_fwsig=enforce`
or `kacs_fwsig=log` override. An override lasts one boot and needs only
access to the bootloader, which is why it is recorded apart from the mode
itself. An unrecognised `kacs_fwsig=` value is ignored with a kernel
warning and leaves the origin `compiled-default`.

**Carried by:**

No event carries this field yet.

## <a id="firmware.result"></a>`firmware.result`

- **Type:** `str.enum`
- **Values:** `allowed` · `unsigned` · `no-key-match` · `below-tcb` · `unverifiable` · `probe-failed`
- **Set:** open
- **Asserted:** no
- **Carried in:** the payload
- **Defined in:** `kacs.evman`

The verdict on a firmware load, named for its `KACS_FW_*` code. `allowed`
is the only passing verdict: the blob verified against a built-in key at
the PeiosTcb tier. `unsigned` means the file carried no signature,
`no-key-match` that it was signed but no built-in key verified it,
`below-tcb` that a key verified it at a lower tier, `unverifiable` that
verification could not run, and `probe-failed` that the signature
material could not be read.

**A failing verdict is not a refusal under `log` policy.** Whether the
blob was loaded is `firmware.policy-mode`'s to say; this field is what the
kernel concluded about the blob either way. `unverifiable` and
`probe-failed` fail rather than pass on purpose: a verification that
cannot run must not become the way around it.

**Carried by:**

No event carries this field yet.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
