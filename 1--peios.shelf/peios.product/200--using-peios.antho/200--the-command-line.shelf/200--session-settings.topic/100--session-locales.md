---
title: Choosing Session Locales
type: how-to
description: Select language and regional conventions for new console, desktop, and SSH sessions.
related:
  - peios/security-tools/my-settings
  - peios/system-tools/system-settings
  - peios/terminal-sign-in/using-a-console
---

A locale controls character handling, sorting, and regional formats such as
dates and numbers. It is separate from a console keyboard layout, console
font, or the desktop clock's 12-hour or 24-hour display preference.

## Before you start

Install the locale data needed by the intended sessions. `locale -a` lists
available locales when the locale tools are installed. Installing language
data does not select it. The Peios session resolver falls back to `C.UTF-8`;
a minimal image must supply its locale data for that fallback to work.

Choose the scope: machine defaults affect users without an override, while
personal preferences affect one account. You need write access to the chosen
registry key and destination layer. Record the old values before changing
individual format categories.

## Select and verify a locale

1. For personal preferences, open [My
   Settings](~peios/security-tools/my-settings) and choose **Language &
   Formats**. For machine defaults, use [System
   Settings](~peios/system-tools/system-settings), **Language & Keyboard**.
2. Choose an installed language and the desired formats. Read the saved
   outcome. The forms write the language and their format categories
   together; use the registry interface for a change to only one category.
3. Keep existing work safe, then start a new session through the intended
   client. Rejoining an existing browser session does not refresh its
   process environments.
4. Inspect that new session:

   ```sh
   locale
   locale charmap
   locale -k decimal_point
   ```

Check the selected language, character set, and category values, not only the
saved registry fields. An application can make its own locale choice.

## Category precedence

Machine preferences live under `Machine\System\Locale`; account
preferences live under `Users\<SID>\Locale`. Read those keys' registry
manuals for supported values and types. authd prepares the private user root
at sign-in; it does not replace an existing root's descriptor.

A valid personal value overrides the same machine value. Categories without
an explicit value use `LANG`. Changing personal `LANG` alone does not remove
a machine category override. For example, a machine `LC_NUMERIC` can keep its
number format even when the account selects another language.

**System Default** removes a personal language override. **Match Language**
removes personal format overrides, so machine category overrides can still
apply. To select one installed locale for language and all categories handled
by the form, select it explicitly in both lists.

Wrong types, malformed names, and unavailable locale data are diagnosed and
ignored, leaving the preceding valid default. A locale name is not a path.
`LC_ALL`, `LANGUAGE`, and `LOCPATH` are not stored session preferences.
For a one-command override, an environment setting such as `LC_ALL=C` can
still be appropriate.

## Client and service boundaries

Console sign-in and new GXWI sessions clear inherited locale overrides before
applying registry preferences. Console `login -p` refreshes locale even while
preserving other environment values.

SSH applies the registry preferences as defaults. Explicit environment entries
permitted by SSH configuration, user environment files, or administrator
`SetEnv` settings can override them for that session. Check the effective
result through the actual SSH route.

These settings do not rewrite running process environments or become peinit's
global service environment. Services need their own documented configuration.
