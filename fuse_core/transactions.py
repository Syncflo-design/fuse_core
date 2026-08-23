"""Which Intacct definition each Fuse process posts to.

Every Intacct company names its transaction definitions differently. Leadertread calls its
goods receipt "Goods received voucher"; the donor's company called the same thing "PO
Receiver-Inventory". A name that is right for one client is wrong for the next, and the
rejection it causes names no field — so nothing here is a constant and nothing is defaulted
from another client.

Two halves:

  * `Intacct Transaction Definition` mirrors what the company actually has, read from
    Intacct. That is the picker.
  * The Transactions table on Intacct Settings maps one Fuse process to one of those
    definitions. That is the client's choice.

`definition_for` is what the postings call. It refuses rather than guesses.

Core owns the picker, the table and the rules. It declares no processes of its own: what
needs mapping belongs to the app that posts it, and each contributes through the
`fuse_processes` hook. That is what lets the table grow as apps are added without core
knowing what a goods receipt is.
"""

import frappe

from fuse_core import gateway
from fuse_core.gateway import val


def all_processes():
	"""Every process any installed Fuse app declares, in app order.

	Resolved on every call rather than at import: hooks need an app context, and there is
	none while this module is still being imported.

	A contributor that raises is skipped rather than allowed to take the settings page down
	with it. Its process is then simply not on the page — and anything that tries to post it
	is refused by definition_for, which is the safe direction.
	"""
	registry = []
	seen = set()

	for method in frappe.get_hooks("fuse_processes") or []:
		try:
			contributed = frappe.get_attr(method)() or []
		except Exception:
			frappe.log_error(
				title=f"Fuse: could not read processes from {method}", message=frappe.get_traceback()
			)
			continue

		for process in contributed:
			# First declaration wins, so a later app cannot redefine another's process and
			# quietly change what it posts to.
			if process.get("key") and process["key"] not in seen:
				seen.add(process["key"])
				registry.append(dict(process))

	return registry


def sync_processes():
	"""Make the settings table match the registry, without touching what is mapped.

	Runs on every migrate. A client's choice is never overwritten; only rows that do not
	exist yet are created, and only they take a seed. Rows belonging to an app that has been
	uninstalled drop off, so the page never asks anyone to map something nothing posts.
	"""
	if not frappe.db.exists("DocType", "Intacct Transaction Mapping"):
		return

	settings = frappe.get_single("Intacct Settings")
	# Same reasoning as modules.sync_modules: seeding is a convenience and must never be
	# able to fail a migrate.
	settings.flags.ignore_mandatory = True
	settings.flags.ignore_validate = True
	chosen = {row.process_key: row.definition for row in settings.get("transaction_mappings") or []}

	settings.set("transaction_mappings", [])
	for process in all_processes():
		definition = chosen.get(process["key"])

		# Seed only a row that has never existed, and only where the definition is really on
		# this company. Writing a name Intacct does not have would put a broken value in
		# front of an admin and look like a considered choice.
		if process["key"] not in chosen and process.get("seed"):
			if frappe.db.exists("Intacct Transaction Definition", process["seed"]):
				definition = process["seed"]

		settings.append(
			"transaction_mappings",
			{
				"process_key": process["key"],
				"label": process["label"],
				"description": process.get("description"),
				"required": process.get("required") or 0,
				"definition": definition,
			},
		)

	settings.flags.ignore_permissions = True
	settings.save(ignore_permissions=True)


def definition_for(key):
	"""The Intacct definition this process posts to, or a refusal saying so.

	Refuses rather than falling back to the name that used to be hardcoded. A fallback would
	post to whatever the donor's company called it — silently, on a client where that name
	means nothing or, worse, means something else.
	"""
	settings = frappe.get_cached_doc("Intacct Settings")
	for row in settings.get("transaction_mappings") or []:
		if row.process_key == key and row.definition:
			return row.definition

	label = key
	for process in all_processes():
		if process["key"] == key:
			label = process.get("label") or key
			break

	frappe.throw(
		f"No Intacct definition is mapped for “{label}”, so this cannot be posted.\n\n"
		"Set it under Transactions on Intacct Settings. The list shows the definitions "
		"this company actually has — run the definitions sync first if it is empty.",
		title="Intacct definition not mapped",
	)


@frappe.whitelist()
def mapping_status():
	"""What is mapped and what is not — for checking a new site before anyone posts."""
	settings = frappe.get_cached_doc("Intacct Settings")
	mapped = {row.process_key: row.definition for row in settings.get("transaction_mappings") or []}
	processes = all_processes()
	return {
		"processes": [
			{
				"key": process["key"],
				"label": process["label"],
				"required": bool(process.get("required")),
				"definition": mapped.get(process["key"]),
				"ready": bool(mapped.get(process["key"])),
			}
			for process in processes
		],
		"unmapped": [
			process["label"]
			for process in processes
			if process.get("required") and not mapped.get(process["key"])
		],
	}


# ──────────────────────────────────────────────────────────────────────────────
# The picker — what this Intacct company actually has
# ──────────────────────────────────────────────────────────────────────────────


def _changed(doc):
	"""True when an in-memory doc differs from what is stored.

	Saving unconditionally would bump `modified` on every definition on every daily run,
	which makes a quiet mirror look like someone has been editing configuration.
	"""
	if doc.is_new():
		return True

	stored = frappe.db.get_value(doc.doctype, doc.name, "*", as_dict=True) or {}
	skip = (
		"modified",
		"modified_by",
		"creation",
		"owner",
		"idx",
		"_user_tags",
		"_comments",
		"_assign",
		"_liked_by",
		"docstatus",
	)
	for field in doc.meta.get_valid_columns():
		if field in skip:
			continue
		if str(stored.get(field) or "") != str(doc.get(field) or ""):
			return True
	return False


@frappe.whitelist()
def sync_transaction_definitions(company=None):
	"""Mirror every transaction definition this company has, so processes can PICK one.

	Purchasing, inventory and order entry together, because a Fuse process cares which
	document it posts and not which Intacct module the definition happens to live in.

	A mirror, not an archive: definitions Intacct no longer reports are removed. Leaving
	them would offer an admin a name that fails the moment it is used.

	Field sets are attempted rich and fall back to the three every *DOCUMENTPARAMS object is
	known to accept, so one unrecognised field name on one object returns a shorter answer
	instead of nothing at all.
	"""
	sources = {
		"Purchasing": (
			"PODOCUMENTPARAMS",
			["RECORDNO", "DOCID", "DESCRIPTION", "DOCCLASS", "STATUS", "ENABLE_SEQNUM",
			 "UPDATES_INV", "CREATETYPE"],
		),
		"Inventory": (
			"INVDOCUMENTPARAMS",
			["RECORDNO", "DOCID", "DESCRIPTION", "DOCCLASS", "STATUS", "ENABLE_SEQNUM",
			 "UPDATES_INV", "CREATETYPE", "UPDATES_COST", "IN_OUT"],
		),
		"Order Entry": (
			"SODOCUMENTPARAMS",
			["RECORDNO", "DOCID", "DESCRIPTION", "DOCCLASS", "STATUS", "ENABLE_SEQNUM",
			 "UPDATES_INV", "CREATETYPE"],
		),
	}

	seen, problems = [], []

	for source, (obj, wanted) in sources.items():
		try:
			rows = gateway.query(obj, wanted, company=company)
		except Exception:
			try:
				rows = gateway.query(obj, ["DOCID", "DOCCLASS", "STATUS"], company=company)
			except Exception as err:
				# One area failing must not cost the others. A company without order entry
				# configured is normal, not an error worth aborting on.
				problems.append(f"{obj}: {err}")
				continue

		for row in rows:
			definition_id = val(row, "DOCID")
			if not definition_id:
				continue
			seen.append(definition_id)

			values = {
				"description": val(row, "DESCRIPTION"),
				"source": source,
				"doc_class": val(row, "DOCCLASS"),
				"status": val(row, "STATUS"),
				"create_type": val(row, "CREATETYPE"),
				"auto_numbered": val(row, "ENABLE_SEQNUM"),
				"updates_inventory": val(row, "UPDATES_INV"),
				"updates_cost": val(row, "UPDATES_COST"),
				"in_out": val(row, "IN_OUT"),
				"intacct_recordno": val(row, "RECORDNO"),
			}

			if frappe.db.exists("Intacct Transaction Definition", definition_id):
				doc = frappe.get_doc("Intacct Transaction Definition", definition_id)
				doc.update(values)
				if _changed(doc):
					doc.save(ignore_permissions=True)
			else:
				doc = frappe.new_doc("Intacct Transaction Definition")
				doc.definition_id = definition_id
				doc.update(values)
				doc.insert(ignore_permissions=True)

	removed = 0
	for name in frappe.get_all(
		"Intacct Transaction Definition",
		filters={"name": ["not in", seen or [""]]},
		pluck="name",
	):
		frappe.delete_doc("Intacct Transaction Definition", name, ignore_permissions=True, force=True)
		removed += 1

	frappe.db.commit()

	# The picker is only useful once the processes that read it exist.
	sync_processes()

	return {
		"definitions": len(seen),
		"removed": removed,
		"problems": problems,
		"unmapped": mapping_status()["unmapped"],
	}
