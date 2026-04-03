---
title: Updates
---

# Updates

App updates are handled as an image update workflow, not as a live in-container
`git pull`.

The recommended sequence is:

1. Update the selected app branches.
2. Set a new `CUSTOM_TAG`.
3. Build the updated custom image.
4. Restart the stack.
5. Run `migrate` on the site if required by the app change.

The wizard keeps the current `frappe_branch` visible while you update apps so
you can see the base version the stack is built against.

`CUSTOM_TAG` is stored in the stack `.env` file. The Compose stack reads that
value on the next start or restart, so the tag change becomes effective once the
image has been rebuilt and the stack is restarted.

For now, this update flow focuses on app branch changes. A separate Frappe base
version update flow can be added later without changing the overall model.
