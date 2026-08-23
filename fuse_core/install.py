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

	frappe.db.commit()
	return seeding
