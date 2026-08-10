---
title: Build a shared checklist
type: how-to
description: Add a persistent, live-updating checklist to a plain static site with one wispist.json declaration and the built-in browser client.
related:
  - wispist/getting-started/what-is-wispist
  - wispist/reference/wispist-json
  - wispist/reference/browser-api
  - wispist/using-wispist/live-updates
---

This page builds the smallest useful Wispist site: a checklist that persists and updates in every open browser. The site has no build step and no connection configuration.

## Declare the collection

Create `wispist.json` at the root of the site bundle:

```json
{
  "version": 1,
  "collections": {
    "before-you-go": {
      "access": "shared",
      "limits": {
        "maxDocuments": 250,
        "maxDocumentBytes": 4096
      }
    }
  }
}
```

The `shared` profile lets every viewer read and change the collection. Use it only when that is the intended product behavior. The two limits lower Wispist's installation defaults for this collection.

## Write the page

Create `index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Before you go</title>
  <script src="/app.js" defer></script>
</head>
<body>
  <main>
    <h1>Before you go</h1>

    <form id="new-item">
      <label>
        New item
        <input name="text" maxlength="180" required>
      </label>
      <button>Add</button>
    </form>

    <p id="status" aria-live="polite">Loading…</p>
    <ul id="items"></ul>
  </main>
</body>
</html>
```

Do not add the Wispist client script yourself on Wispdeck. Wispdeck inserts it before the page's own `script` element, so `wispist` exists when `app.js` runs.

## Add and render documents

Create `app.js`:

```js
const checklist = wispist.collection("before-you-go");
const form = document.querySelector("#new-item");
const list = document.querySelector("#items");
const status = document.querySelector("#status");

let documents = new Map();

function render(items) {
  documents = new Map(items.map((item) => [item.id, item]));
  list.replaceChildren();

  for (const item of items) {
    const row = document.createElement("li");
    const checkbox = document.createElement("input");
    const text = document.createElement("span");

    checkbox.type = "checkbox";
    checkbox.checked = Boolean(item.data.done);
    checkbox.dataset.id = item.id;
    text.textContent = String(item.data.text);
    row.append(checkbox, text);
    list.append(row);
  }

  status.textContent = `${items.length} shared item(s)`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = new FormData(form).get("text").trim();
  if (!input) return;

  try {
    await checklist.add({ text: input, done: false });
    form.reset();
  } catch (error) {
    status.textContent = error.detail || "The item could not be added.";
  }
});
```

`add` creates a generated document ID and returns the complete document envelope. The client supplies the required idempotency key automatically.

## Apply safe updates

Add a delegated change listener:

```js
list.addEventListener("change", async (event) => {
  const checkbox = event.target.closest('input[type="checkbox"][data-id]');
  const item = checkbox && documents.get(checkbox.dataset.id);
  if (!item) return;

  checkbox.disabled = true;
  try {
    await checklist.update(item, { done: checkbox.checked });
  } catch (error) {
    checkbox.checked = Boolean(item.data.done);
    status.textContent = error.code === "revision_conflict"
      ? "Somebody else changed that item. Try again from the latest version."
      : error.detail || "The item could not be changed.";
  } finally {
    checkbox.disabled = false;
  }
});
```

`update` accepts the observed document, not only its ID. It shallow-merges the new fields locally and sends a replacement conditional on `item.revision`. A stale revision becomes a typed [revision conflict](~wispist/problems/revision-conflict).

## Subscribe

Start the live collection at the end of `app.js`:

```js
const unsubscribe = checklist.subscribe(render, {
  onError(error) {
    status.textContent = error.detail || "Live updates are unavailable.";
  },
});
```

`subscribe` returns immediately. It lists every page, opens a change stream from that list cursor, maintains a document map, and calls `render` with the initial state and every later state.

Call `unsubscribe()` when a long-lived page no longer needs the collection. Closing a page closes its EventSource automatically.

## Upload and test

Put the three files at the ZIP root:

```text
checklist.zip
├── index.html
├── app.js
└── wispist.json
```

Upload the archive as a Wispdeck site draft. In preview, the checklist uses draft data. Publish the release, open the public site in two independent browser windows, and add or check an item in one. The other should update without a refresh.

When a later draft exists, changes made in Draft remain separate. Select Current to see live data in read-only mode. Publishing that draft changes the code and declaration while leaving the public checklist intact.
