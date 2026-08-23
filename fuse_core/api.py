"""Whitelisted entry points for Fuse Core."""

import frappe


@frappe.whitelist()
def setup():
	"""Re-apply core's site configuration — the module switch table.

	Exists because after_migrate does not reliably fire on a Frappe Cloud deploy, and
	without this, repairing that needs bench access.
	"""
	frappe.only_for("System Manager")

	from fuse_core.install import after_install

	return after_install()
