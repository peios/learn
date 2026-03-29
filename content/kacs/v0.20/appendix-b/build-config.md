---
title: Build Configuration
order: 3
---

KACS requires the following kernel configuration:

| Option | Value | Reason |
|---|---|---|
| CONFIG_SECURITY_KACS | y | Enables KACS LSM. |
| CONFIG_RUST | y | Rust language support for the AccessCheck engine. |
| CONFIG_SECURITY_SELINUX | n | No other MAC LSMs. |
| CONFIG_SECURITY_APPARMOR | n | No other MAC LSMs. |
| CONFIG_BPF_LSM | n | No runtime-attached LSM programs. |
| CONFIG_LSM | "commoncap,kacs" | Exact LSM stack. |
| CONFIG_STRICT_DEVMEM | y | Restrict /dev/mem to I/O regions (PIP defense-in-depth). |
| CONFIG_MODULE_SIG_FORCE | y | Require signed kernel modules (PIP defense-in-depth). |

KACS MUST verify the LSM stack at initialization and refuse to activate if any unexpected LSM is present.

CONFIG_SECURITY_PATH is not required. KACS does not register `security_path_*` callbacks.
