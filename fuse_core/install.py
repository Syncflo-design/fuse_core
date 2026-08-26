"""Site configuration core owns — currently the module switch table.

Wired to after_install AND after_migrate, and exposed as fuse_core.api.setup, because
after_migrate has been observed not to fire on a Frappe Cloud deploy. Everything here is
idempotent, so re-running only closes gaps.
"""

import frappe

from fuse_core import modules, transactions


def after_install():
	"""Put core's configuration in step with whatever apps are installed.

	Seeding runs from core rather than from each feature app so that a site with three Fuse
	apps seeds the table once, not three times, and so that removing an app takes its
	switches with it on the next migrate.

	A failure here must never take a deploy down: the switches are a launcher preference,
	and a missing row costs an admin one click.
	"""
	seeding = {}
	for name, seed, count in (
		("modules", modules.sync_modules, modules.all_modules),
		("processes", transactions.sync_processes, transactions.all_processes),
	):
		try:
			seed()
			seeding[name] = len(count())
		except Exception:
			frappe.log_error(
				title=f"Fuse Core: could not seed the {name} table", message=frappe.get_traceback()
			)
			seeding[name] = "failed"

	seeding["approver_role"] = _approver_role()

	frappe.db.commit()
	return seeding


def _approver_role():
	"""The role that signs off a discretionary support ticket.

	Created empty and assigned by the client — we have no business deciding who speaks for
	them. Until somebody holds it the approval gate stays open and tickets go straight
	through, which is deliberate: a gate nobody can open is not a control.
	"""
	from fuse_core.fuse_core.doctype.fuse_support_ticket.fuse_support_ticket import APPROVER_ROLE

	if frappe.db.exists("Role", APPROVER_ROLE):
		return APPROVER_ROLE

	try:
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": APPROVER_ROLE,
				"desk_access": 1,
				# Not restricted to a module: the people who decide what is worth asking for
				# are rarely the people who live in one.
				"is_custom": 1,
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			title="Fuse Core: could not create the support approver role",
			message=frappe.get_traceback(),
		)
		return "failed"

	return APPROVER_ROLE
