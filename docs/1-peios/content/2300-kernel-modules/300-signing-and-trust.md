---
title: Module Signing and Trust
type: concept
description: How the kernel verifies module signatures, the three trusted-key sources, the build-floor + registry knob policy model, and Secure Boot integration.
related:
  - peios/kernel-modules/loading-and-unloading
  - peios/kernel-modules/overview-and-design
  - peios/integrity/secure-boot
---

Module signing is the second of two gates protecting kernel-code injection. Where [SeLoadDriverPrivilege](../privileges/load-driver) gates *who* can request a load, signature verification gates *what* may be loaded — even a privileged caller cannot install a module the kernel does not trust.

## Signature mechanism

A signed module has a PKCS#7 signature blob appended to the end of the `.ko` file, plus a small marker indicating the signature is present. When the kernel processes a load request, it:

1. Detects the appended signature marker.
2. Strips the signature off the loaded image (the module's actual code/data ends just before the marker).
3. Computes the module's hash (SHA-256 / SHA-384 / SHA-512 — algorithm declared in the signature).
4. Verifies the signature against the kernel's trusted-key set.
5. If valid, proceeds with the load. If invalid or missing, applies signing policy (see below).

The signature scheme follows Linux's exactly so that modules signed by standard Linux signing tools work on Peios kernels (modulo the trusted-key configuration).

## Trusted keys

Peios maintains three keyrings analogous to Linux's, with policies suited to a server-tier deployment:

| Keyring | Source | Mutability | Trust posture |
|---|---|---|---|
| **Build-in trusted keys** (`.builtin_trusted_keys`) | Compiled into the kernel image at build time | Immutable at runtime | The root of trust. The Peios distribution signing key is here. |
| **Secondary trusted keys** (`.secondary_trusted_keys`) | Added at runtime, but only signable by an existing trusted key | Runtime-extensible (with cryptographic gate) | Used to add additional signing keys whose authority chains back to a build-in key. |
| **Machine Owner Keys (MOK)** | UEFI-managed via shim, enrolled through reboot-to-shim console flow | Per-machine, requires console access to extend | Used to enroll customer-owned signing keys for locally-built modules under Secure Boot. |

A module signature is valid if it was signed by **any** key in any of these three keyrings. There is no preference order — keys from any source carry equal authority once they are in their respective keyring.

### Build-in trusted keys

The build-in keyring is set up at kernel build time. It always contains the Peios distribution signing key (used to sign all modules shipped in standard Peios kernel images and OOT-vendor packages produced by the Peios build pipeline). Customers who build their own Peios kernel can replace the build-in key with their own — it lives in the source as a build artifact.

This keyring **cannot be modified at runtime**. There is no syscall, no registry knob, no `keyctl` operation that adds keys to it. The only way to extend the build-in trust set is to rebuild the kernel.

### Secondary trusted keys

The secondary keyring exists for the use case "vendor publishes a signing key, customer's signing-policy admin wants the kernel to trust modules signed by that vendor." A new key may be added to the secondary keyring at runtime, but only if **the new key is itself signed by a key already in the build-in or secondary keyring**.

This means the trust chain is always rooted in `.builtin_trusted_keys`. There is no "add an arbitrary key" path — the cryptographic gate ensures all secondary keys transitively chain to a build-time-trusted root.

In practice, the secondary keyring is rarely used on standard Peios server builds because the Peios distribution build pipeline produces signed packages for OOT modules itself, signed by the build-in distribution key. The secondary keyring matters more for environments with multiple vendors operating internal cross-signing relationships.

### Machine Owner Keys (MOK)

The MOK list lives in UEFI NVRAM and is enrolled through the **shim MOK Manager** — a UEFI-resident program that prompts at the console during reboot. The enrollment flow:

1. From a running system: `mokutil --import key.der` writes the proposed key to a UEFI variable, requires a password set by the administrator.
2. Administrator reboots.
3. shim's MOK Manager runs at boot, prompts at the console for the password set in step 1.
4. Administrator confirms; shim writes the key into the kernel keyring.
5. Reboot completes; the kernel now trusts modules signed by the new MOK.

The console prompt is the security gate. A purely-remote attacker who has gained `SeTcbPrivilege` cannot complete MOK enrollment without involving someone at the physical or out-of-band-management console.

MOK is a Secure Boot concept. It requires:

- UEFI Secure Boot enabled.
- The Peios kernel image signed by a key trusted by shim (typically Microsoft's, via shim's standard chain).
- The shim itself trusted by the firmware.

Non-Secure-Boot Peios systems have no MOK list and no shim. They get build-in + secondary only.

## Signing policy

The kernel's response to an unsigned module, or a module signed by a key not in any trusted keyring, is governed by the **signing policy**. Three modes:

| Mode | Behaviour |
|---|---|
| `enforce` | Unsigned modules and modules with invalid signatures are rejected. Load fails with `EKEYREJECTED`. |
| `warn` | Unsigned modules load but the kernel taints itself (`TAINT_UNSIGNED_MODULE`) and emits an audit event. Modules with invalid signatures are still rejected. |
| `permissive` | Unsigned modules load silently (no taint, no audit). Modules with invalid signatures are still rejected. |

`permissive` is rarely used outside lab/test environments — Linux distros effectively never run in this mode in production, and Peios doesn't either.

### The build-time floor

The kernel build sets a **floor** for the policy: a minimum strictness that the running kernel will never go below regardless of any registry value or runtime API. The floor is set by `CONFIG_PEIOS_MODULE_SIG_FLOOR={enforce|warn|permissive}` at build time.

Standard Peios server build defaults the floor to `warn` — matching Linux's effective default behaviour (verify if present, accept unsigned with taint) for compatibility with workloads that don't have signing infrastructure. Hardened build variants may bake the floor at `enforce`.

### The runtime knob

The registry knob `\System\Modules\SigningPolicy` (driven by ksyncd) sets the *currently active* policy, subject to the constraint that **the active policy can only be at-or-stricter than the build floor**. The kernel applies the stricter of {floor, knob}.

So on a standard build (floor `warn`):

- Knob `permissive` → ignored, runs at `warn`.
- Knob `warn` → runs at `warn`.
- Knob `enforce` → runs at `enforce`.

On a hardened build (floor `enforce`), the knob has no effect at all — the kernel is always at `enforce`.

### One-way ratchet within a boot

Once the runtime state reaches `enforce`, it stays at `enforce` until reboot. The kernel does not honour requests to weaken the active policy at runtime, even if the registry knob is changed back. The reasoning is the same as Linux's `module.sig_enforce` semantics: an attacker who has compromised something with registry-write authority should not be able to weaken signing without a reboot, which itself produces a recovery opportunity.

A reboot reads the registry fresh and applies whatever the knob is currently set to (subject to the floor).

### SD on the policy knob

`\System\Modules\SigningPolicy` is a security-relevant policy key. Its DACL grants `KEY_SET_VALUE` only to `LocalSystem` and `Administrators`. There is no privilege gate beyond the SD; the principal restriction is the gate.

The knob is a candidate for **Superlock** (a future Peios mechanism that prevents modification of flagged registry values outside Safe Mode or Recovery Mode), which would mean even `Administrators` on a running system could not weaken the signing policy without rebooting into a recovery context.

### Future: registry-managed trusted keys

Today, no fourth keyring source exists — registry-managed trusted keys are not implemented. The MOK reboot-to-shim flow is the supported mechanism for runtime trust extension.

When Superlock ships, a registry-managed trusted-key source becomes viable: Superlock-flagged trusted-key entries in `\System\Modules\TrustedKeys` would have the same security posture as MOK (un-modifiable from a running normally-booted system) without requiring Secure Boot. Until then, the registry path is not opened — the security guarantee Linux's MOK provides cannot be matched by a runtime-mutable registry source alone.

## Forced module loading

Linux's `init_module` accepts a `MODULE_INIT_IGNORE_MODVERSIONS` flag and a `MODULE_INIT_IGNORE_VERMAGIC` flag — "load this module even if the version-magic or modversions don't match." These flags do not bypass signature verification, but they bypass other consistency checks.

Standard Peios server builds **do not honour these flags**. The kernel rejects ignore-modversions and ignore-vermagic at the same level it rejects forced unload — the capability is compiled out. Module compatibility is a load-time invariant; there is no escape.

## Signature format details

| Field | Notes |
|---|---|
| Signature blob | PKCS#7 (CMS), appended after module image |
| Hash algorithm | SHA-256, SHA-384, or SHA-512 (declared in PKCS#7 header) |
| Trailer marker | `~Module signature appended~\n` literal string |
| Signature length | 4-byte little-endian, immediately before trailer marker |

This format is byte-compatible with Linux modules. A module signed by a key that's also enrolled in a Peios kernel's trusted set loads on both kernels.

## Audit events

Module signature verification produces these audit events:

- **Successful signature verification** — at `info` tier, default `disabled` (volume is high; ops can enable for forensic environments).
- **Signature missing under `warn` policy** — taint event, default `enabled`. Includes module name and the loading caller's token.
- **Signature invalid (any policy)** — security event, always `enabled` regardless of registry config. Includes module name, loading caller's token, and the failed-key information from the verification attempt.
- **Module load rejected by `enforce` policy** — security event, always `enabled`.

## See also

- [Loading and unloading](loading-and-unloading) — where signature verification fits in the load lifecycle.
- [Tainting and observability](tainting-and-observability) — the taint bits set when unsigned modules load.
- [Secure Boot](../integrity/secure-boot) — the firmware-level trust chain that anchors MOK.
