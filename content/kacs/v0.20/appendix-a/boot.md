---
title: Boot Sequence
order: 5
---

1. **LSM registration.** KACS registers as the second LSM after commoncap. Blob sizes are declared. Hook table is installed. KACS verifies the LSM stack — if any unexpected LSM is present, KACS MUST NOT activate.

2. **SYSTEM session.** Session 0 is created: logon type SERVICE, user SID `S-1-5-18`, auth package "Negotiate". Logon SID `S-1-5-5-0-0` is generated.

3. **SYSTEM token.** The SYSTEM token is minted: user `S-1-5-18`, all privileges enabled, integrity System, token type Primary, logon session 0. Groups include `S-1-5-32-544` (Administrators), `S-1-1-0` (Everyone), `S-1-5-11` (Authenticated Users).

4. **Init attachment.** The SYSTEM token is attached to the init process's credential. All processes forked from init inherit the SYSTEM token.

5. **Capability assertion.** The DAC bypass and credential management capabilities are asserted on the SYSTEM credential.

6. **Userspace transition.** peinit starts. It launches authd. authd authenticates service principals, creates logon sessions and tokens, and assigns tokens to services. From this point, services run with their own tokens.

> [!INFORMATIVE]
> The window between steps 4 and 6 is the "everything is SYSTEM" phase. During this phase, all file access succeeds (SYSTEM has all rights). The window ends when authd starts assigning real tokens. No security-sensitive user-facing services SHOULD be started until authd is running.
