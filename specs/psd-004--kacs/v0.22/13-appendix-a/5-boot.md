---
title: Boot Sequence
---

1. **LSM registration.** PKM registers as an LSM (after commoncap, which is implicit). Blob sizes are declared. Hook table is installed. PKM verifies the LSM stack — if any MAC LSM (SELinux, AppArmor, SMACK, TOMOYO) or BPF LSM is present, PKM MUST NOT activate. Non-MAC LSMs (landlock, lockdown, yama, integrity) are accepted.

2. **SYSTEM LogonSession.** LogonSession 0 is created by direct kernel initialization (not via `kacs_create_logon_session` — no process or privilege exists yet): logon_session_id = 0, logon type SERVICE, user SID `S-1-5-18`, auth package "Negotiate". Logon SID `S-1-5-5-0-0` is derived from logon_session_id.

3. **SYSTEM token.** The SYSTEM token is minted by direct kernel initialization (not via `kacs_create_token`): user `S-1-5-18`, all privileges from the privilege catalog enabled, integrity System, token type Primary, impersonation level Anonymous, auth_id 0 (LogonSession 0), source `PeiosKrn` (source LUID = 0), projected UID 0, projected GID 0, elevation_type Default, mandatory_policy `NO_WRITE_UP | NEW_PROCESS_MIN` (0x0003), interactivity_scope 0, expiration 0 (no expiry), origin LUID 0, audit_policy 0, write_restricted false, user_deny_only false, restricted_sids empty, confinement_sid absent, confinement_exempt false, isolation_boundary false, projected_supplementary_gids empty. Groups:
   - `S-1-5-32-544` (Administrators) — SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED | SE_GROUP_OWNER
   - `S-1-1-0` (Everyone) — SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED
   - `S-1-5-11` (Authenticated Users) — SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED
   - `S-1-2-0` (Local) — SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED
   - `S-1-5-5-0-0` (Logon SID) — SE_GROUP_MANDATORY | SE_GROUP_ENABLED_BY_DEFAULT | SE_GROUP_ENABLED | SE_GROUP_LOGON_ID

   Default DACL (for objects created by SYSTEM): ALLOW SYSTEM GENERIC_ALL, ALLOW BUILTIN\Administrators GENERIC_ALL.

   The SYSTEM token's own SD (controlling who can open a handle to this token): owner SYSTEM, DACL: ALLOW SYSTEM (TOKEN_QUERY | TOKEN_ADJUST_PRIVILEGES | TOKEN_ADJUST_GROUPS | TOKEN_ADJUST_DEFAULT), ALLOW SYSTEM TOKEN_ALL_ACCESS, ALLOW BUILTIN\Administrators TOKEN_ALL_ACCESS. This is an explicit bootstrap SD — the standard default template (user + creator + SYSTEM) would produce duplicate SYSTEM ACEs and no Administrators ACE, so the SYSTEM token uses a hardcoded SD that grants Administrators full control for manageability.

   > [!INFORMATIVE]
   > When domain/federation support is added, the SYSTEM token should also include `S-1-5-15` (This Organization). This SID is omitted in v0.20 because no domain controller exists to determine organizational membership. authd in a federated configuration will be responsible for adding it.

4. **Init attachment.** The SYSTEM token is attached to the init process's credential. All processes forked from init inherit the SYSTEM token.

5. **Capability assertion.** The DAC bypass and credential management capabilities are asserted on the SYSTEM credential.

6. **Userspace transition.** peinit starts. It launches authd. authd authenticates service principals, creates LogonSessions and tokens, and assigns tokens to services. From this point, services run with their own tokens.

> [!INFORMATIVE]
> The window between steps 4 and 6 is the "everything is SYSTEM" phase. During this phase, all file access succeeds (SYSTEM has all rights). The window ends when authd starts assigning real tokens. No security-sensitive user-facing services SHOULD be started until authd is running.
