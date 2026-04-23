---
title: Build Configuration
---

KACS requires the following kernel configuration:

| Option | Value | Reason |
|---|---|---|
| CONFIG_SECURITY_PKM | y | Enables the PKM LSM (which includes KACS). |
| CONFIG_RUST | y | Rust language support for the AccessCheck engine. |
| CONFIG_SECURITY_SELINUX | n | No MAC LSMs. |
| CONFIG_SECURITY_APPARMOR | n | No MAC LSMs. |
| CONFIG_SECURITY_SMACK | n | No MAC LSMs. |
| CONFIG_SECURITY_TOMOYO | n | No MAC LSMs. |
| CONFIG_BPF_LSM | n | No runtime-attached LSM programs. |
| CONFIG_LSM | "landlock,lockdown,yama,integrity,pkm" | LSM stack. Non-MAC security LSMs (landlock, lockdown, yama, integrity) are accepted; MAC LSMs are not. commoncap is implicit in the kernel LSM framework and MUST NOT appear in this list. |
| CONFIG_STRICT_DEVMEM | y | Restrict /dev/mem to I/O regions (PIP defense-in-depth). |
| CONFIG_MODULE_SIG_FORCE | y | Require signed kernel modules (PIP defense-in-depth). |

PKM MUST verify the LSM stack at initialization and refuse to activate if any MAC LSM (SELinux, AppArmor, SMACK, TOMOYO) or BPF LSM is present. Non-MAC LSMs are permitted.

CONFIG_SECURITY_PATH is not required. KACS does not register `security_path_*` callbacks.
