"""Which parts of Fuse a client has switched on.

This is a LAUNCHER preference, not a permission. Switching a module off takes its tile
off Fuse Home and nothing else: the doctypes behind it still work, and someone who knows
the URL or uses the awesome bar still gets there. Anything stronger belongs in role
permissions, which a deploy overwrites (see the 2026-05-20 gotcha), or in a guard on the
doctype itself — both bigger decisions than tidying a home page.

Core holds the TABLE and the rules for it. It declares no modules of its own: the
features belong to the apps that implement them, and each one contributes its switches
through the `fuse_modules` hook. Core knowing nothing about Receiving or Projects is what
lets either app be installed, sold or removed on its own.
"""

import frappe


def all_modules():
	"""Every switch any installed Fuse app declares, in app order.

	Resolved on every call rather than at import: hooks need an app context, and there is
	none while this module is still being imported.

	A contributor that raises is skipped rather than allowed to take the settings page down
	with it. Its switch then reads as ON, which is what a site without that app looks like
	anyway.
	"""
	registry = []
	seen = set()

	for method in frappe.get_hooks("fuse_modules") or []:
		try:
			contributed = frappe.get_attr(method)() or []
		except Exception:
			frappe.log_error(
				title=f"Fuse: could not read modules from {method}", message=frappe.get_traceback()
			)
			continue

		for module in contributed:
			# First declaration wins, so a later app cannot redefine another's module and
			# quietly change what its switch governs.
			if module.get("key") and module["key"] not in seen:
				seen.add(module["key"])
				registry.append(dict(module))

	return registry


def module_label(key):
	"""What to call one module in a message to a user. Unknown keys answer with the key."""
	for module in all_modules():
		if module["key"] == key:
			return module.get("label") or key
	return key


def sync_modules():
	"""Make the settings table match the registry, without touching what is switched on.

	Runs on every migrate. New modules arrive switched ON, because a feature that ships
	invisible looks broken rather than optional. Retired ones are dropped, so the page never
	lists something that no longer exists — including everything belonging to an app that
	has been uninstalled.

	A client's own choice is never overwritten — that is the whole point of the table.
	"""
	if not frappe.db.exists("DocType", "Fuse Active Module"):
		return

	settings = frappe.get_single("Intacct Settings")
	# Seeding a settings table must never be the reason a deploy fails. Intacct Settings has
	# required fields, and a save during migrate can throw for reasons that have nothing to
	# do with this table — on a site where credentials are not filled in yet, for instance.
	# A missing row costs an admin one click; a failed migrate costs the whole release,
	# which is what happened on 2026-08-19.
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_validate = True
	chosen = {row.module_key: row.enabled for row in settings.get("active_modules") or []}

	settings.set("active_modules", [])
	for module in all_modules():
		settings.append(
			"active_modules",
			{
				"module_key": module["key"],
				"label": module["label"],
				"description": module.get("description"),
				# Present and set → keep it. Absent → new, so on.
				"enabled": chosen.get(module["key"], 1),
			},
		)

	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)


@frappe.whitelist()
def active_modules():
	"""What is switched on, as {key: True/False}.

	A key missing from the table reads as ON. That matters on a site migrated before the
	table existed, and on the first load after a new module ships — in both cases the honest
	answer is "nobody has turned this off".
	"""
	settings = frappe.get_cached_doc("Intacct Settings")
	chosen = {row.module_key: bool(row.enabled) for row in settings.get("active_modules") or []}
	return {module["key"]: chosen.get(module["key"], True) for module in all_modules()}


def is_active(key):
	"""Whether one module is switched on. Unknown keys are on, for the same reason."""
	return active_modules().get(key, True)
