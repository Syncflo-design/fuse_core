# Fuse Core

The Sage Intacct connection every Fuse app shares: the XML gateway, one set of
credentials, the module switches and the request log.

Base of the Fuse set. `fuse_manufacturing` and `fuse_projects` both sit on it; neither
talks to Intacct itself.

## What it owns

- **`gateway.py`** — the XML transport. Session, query, read, lookup, execute. Everything
  that reaches Intacct goes through here.
- **`rules.py`** — the pure functions the transport depends on: deterministic control IDs,
  result keys, rejection detection, Intacct date parsing.
- **Intacct Settings** — credentials, entity, gateway URL, page size, timeouts. One set,
  however many Fuse apps are installed.
- **Intacct Request Log** — every write, and every read that failed.
- **Fuse Active Module** — the switch table, and the rules for keeping it in step.
- **Intacct Transaction Definition / Mapping** — the definitions this company actually has,
  read from Intacct, and which one each Fuse process posts to.

## What it does not own

No features. Core declares no modules and no processes of its own, and knows nothing about
Receiving, Works Orders or Projects. Each app contributes its switches through the
`fuse_modules` hook and its postable processes through `fuse_processes`, so any of them can
be installed or removed without core changing — and both tables grow as apps are added.

Nothing here links to an ERPNext doctype. That is deliberate — it is what lets core be
the shared base for apps that do.

## Install

Frappe v16. Install core first: the other Fuse apps declare it in `required_apps` and
their migrate assumes the Intacct Settings doctype already belongs to it.

After a Frappe Cloud deploy, `after_migrate` has been seen not to fire. Re-apply the
configuration with `fuse_core.api.setup` (System Manager only).
