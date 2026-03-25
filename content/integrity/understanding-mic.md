---
title: Understanding Mandatory Integrity Control (MIC)
type: concept
order: 10
---

**Mandatory Integrity Control (MIC)** is a trust boundary that sits above the DACL. Even if the DACL would grant access, MIC can deny it based on the relative trust levels of the process and the object.

MIC answers a simple question: is this process trusted enough to modify this object?

## Integrity levels

Every token carries an integrity level. Every object can have one. There are five tiers:

| Level | Typical use |
|---|---|
| **Untrusted** | Processes with no trust — sandboxed or unknown code |
| **Low** | Processes that handle untrusted input (web-facing services, download handlers) |
| **Medium** | Standard user processes — the default for interactive sessions |
| **High** | Administrative processes — elevated tokens |
| **System** | The operating system itself — core services running as SYSTEM |

A token's integrity level is set at creation time and cannot be raised. A process can lower its own integrity level (to reduce its trust) but cannot elevate it.

## The no-write-up rule

The core of MIC is a single rule: **a process cannot write to objects labeled above its integrity level.**

A process running at Medium integrity cannot modify an object labeled High — regardless of what the DACL says. The DACL might grant the process full write access, but MIC overrides it.

By default, MIC only restricts write access. Read and execute are allowed even when the process's integrity level is below the object's label. However, an object's mandatory label can optionally restrict read and execute as well — this is configured per-object through flags on the label.

## Evaluated before the DACL

MIC is checked **before** the DACL walk in the AccessCheck pipeline. If the token's integrity level is below the object's label and the requested operation is restricted, AccessCheck denies the request immediately. The DACL is never consulted.

If MIC passes — because the token's integrity level meets or exceeds the object's label, or because the operation is not restricted — evaluation continues to the DACL as normal.

MIC sets a floor. It cannot grant access, only deny it.

## Where labels come from

An object's integrity label is a special ACE in the SACL — a **mandatory label ACE**. It specifies the integrity level and which operations are restricted (write, read, execute).

Objects without an explicit mandatory label are treated as **Medium** by default. Since most user processes also run at Medium, MIC is transparent in the common case — it only becomes visible when integrity levels diverge.

Setting or changing a mandatory label requires the `SeRelabelPrivilege`. Ordinary users cannot change integrity labels on objects they own — this is system policy, not discretionary.

## What MIC protects against

MIC prevents a lower-trust process from tampering with higher-trust objects. If a web-facing service running at Low integrity is compromised, it cannot modify files or registry keys at Medium or above — even if the DACL would otherwise allow it.

This is a safety net, not a replacement for the DACL. MIC catches the case where the DACL is too permissive for the threat level. A compromised Low-integrity process that has DACL access to a High-integrity object is still blocked. The DACL and MIC work together — the DACL controls who has access, MIC controls the minimum trust required to exercise it.
