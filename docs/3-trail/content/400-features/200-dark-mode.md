---
title: Dark Mode
type: concept
description: Trail supports dark mode with system preference detection, a manual toggle, localStorage persistence, and a no-flash script.
---

Trail has built-in dark mode support. Every element of the UI -- navigation, content, code blocks, admonitions, search results, and diagrams -- adapts to the selected color scheme.

## How dark mode is determined

Trail checks for dark mode preference in this order:

1. **localStorage.** If the key `theme` is set to `"dark"` or `"light"`, that value is used.
2. **System preference.** If no localStorage value exists, Trail checks the `prefers-color-scheme: dark` media query.
3. **Default.** If neither is set, light mode is used.

## The no-flash script

A common problem with client-side dark mode is a flash of light-mode content before JavaScript runs. Trail solves this with an inline script in the `<head>` that runs before the page renders:

```javascript
if (localStorage.getItem('theme') === 'dark' ||
    (!localStorage.getItem('theme') &&
     window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark');
}
```

Because this script is inline (not in an external file), it executes synchronously before the browser paints the page. The `dark` class is on the `<html>` element before any content renders, so there is no flash.

## Manual toggle

The toggle button is in the top navigation bar, between the search input and the mobile menu button. It shows:

- A **sun icon** when dark mode is active (click to switch to light).
- A **moon icon** when light mode is active (click to switch to dark).

Clicking the toggle:

1. Toggles the `dark` class on the `<html>` element.
2. Stores the new preference in localStorage under the key `theme`.
3. Updates the toggle icon.
4. Re-renders any Mermaid diagrams with the appropriate theme.

## Persistence

The theme choice persists in localStorage across page loads and browser sessions. The key is `theme` and the value is either `"dark"` or `"light"`.

Clearing localStorage (or using a private/incognito window) resets to system preference detection.

## How the styling works

Trail uses Tailwind CSS with the `class` dark mode strategy. Every styled element has both light and dark variants:

```html
<div class="bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
```

When the `dark` class is present on the `<html>` element, all `dark:` prefixed utilities take effect.

## Component-specific dark mode behavior

| Component | Light mode | Dark mode |
|---|---|---|
| Page background | White | Near-black (gray-950) |
| Text | Dark gray | Light gray |
| Code blocks | Dracula (dark) | Dracula (dark) -- unchanged |
| Admonitions | Light tinted background | Dark tinted background |
| Search results | White dropdown | Dark gray dropdown |
| Tables | Light borders, white cells | Dark borders, transparent cells |
| Sidebar links | Gray text, blue active | Gray text, blue active |
| Mermaid diagrams | Default theme | Dark theme |

Code blocks use the Dracula theme in both modes, so they always have a dark background.

## Mermaid diagram re-rendering

When the color mode changes, Trail re-renders all Mermaid diagrams. Each diagram element stores its original source text in a `data-mermaid-src` attribute. On theme toggle, Trail:

1. Restores the original source text from the attribute.
2. Removes the `data-processed` attribute so Mermaid treats it as new.
3. Re-initializes Mermaid with the correct theme (`default` or `dark`).
4. Runs Mermaid to re-render all diagrams.

This ensures diagrams use appropriate colors for the current mode.
