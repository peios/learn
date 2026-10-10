---
title: Default apps
type: how-to
description: Choose which app opens each type of file when more than one can, for yourself or for everyone, in Desktop Settings or the registry.
related:
  - peios/desktop-settings/overview
  - peios/desktop-settings/for-all-users
---

When more than one installed app can open a type of file, the **default
app** is the one that opens it when you open the file, for example by
double-clicking it in Gexora. The others stay on the file's right-click
menu.

## Choosing one

In Desktop Settings, **Default Apps** under **For You** lists each type of
file that more than one app can open, by its name and its media type, with
the apps that can open it. Choose one, or **System Default** for the
machine's choice. It applies at once.

A type only one app opens isn't listed: there is nothing to choose. When
no app can be chosen for anything yet, the section says **No Choices**.

## How the default is found

Choices are made for a whole media type, such as `image/png`, or for a
family of them, such as `image/*`. For a file, the first of these that
names an app that can still open it wins:

1. your choice for its exact type;
2. your choice for its family;
3. the machine's choice for its exact type;
4. the machine's choice for its family.

So your choice for every image beats the machine's choice for PNGs. When
none of them applies, the app that opens the file is the first available.
A choice never makes an app open a type it doesn't say it opens, and a
choice naming an app that has since been removed is simply passed over.

## Where they are kept

Each choice is a `REG_SZ` value in `CurrentUser\Generic\Applications\Defaults`
(yours) or `Machine\Generic\Applications\Defaults` (the machine's), named
by the media type and holding the app's id:

```
$ reg set 'CurrentUser\Generic\Applications\Defaults' image/png sz:dev.peios.peitor
```

The whole rule, for anyone writing a program that opens files, is PGSS
[Defaults](~peios/pgss/applications/defaults).

## Where to go next

- [Settings for all users](~peios/desktop-settings/for-all-users)
