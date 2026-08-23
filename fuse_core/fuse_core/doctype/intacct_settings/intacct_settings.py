import frappe
from frappe.model.document import Document


class IntacctSettings(Document):
	def validate(self):
		if self.page_size and self.page_size > 1000:
			frappe.msgprint(
				"Intacct's own guidance is to keep queries under about 1000 records. "
				"Larger pages tend to time out rather than fail cleanly."
			)

	def on_update(self):
		"""Tell the feature apps when the module switches change.

		Without this a switch would only take effect at the next migrate, so an admin would
		turn Receiving off, watch the tile vanish, and find the document still reachable —
		which reads as the setting not working.

		Core cannot call fuse_manufacturing directly; the whole point of core is that it does
		not know which apps are installed. So it announces the change through the
		`fuse_modules_changed` hook and each app does whatever the switch means to it —
		withdrawing document permissions, in Manufacturing's case.

		Only when something actually changed: re-applying permissions on every save of an
		unrelated field is churn, and permission writes are not free.
		"""
		# Not during install or migrate. Each app applies its own state once everything is in
		# place; doing it again from inside a save that migrate triggered meant a seeding step
		# could take the whole deploy down with it.
		if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
			return

		before = self.get_doc_before_save()
		if before is not None:
			was = {row.module_key: row.enabled for row in before.get("active_modules") or []}
			now = {row.module_key: row.enabled for row in self.get("active_modules") or []}
			if was == now:
				return

		for method in frappe.get_hooks("fuse_modules_changed") or []:
			try:
				frappe.get_attr(method)()
			except Exception:
				# One app's reaction failing must not stop the others, and must not fail the
				# save — the switch itself is already stored, and that is what the admin came
				# to do.
				frappe.log_error(
					title=f"Fuse: {method} failed after a module switch changed",
					message=frappe.get_traceback(),
				)
