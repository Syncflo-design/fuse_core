"""Gateway decision logic, with no Frappe and no network.

Every function here is pure: given the inputs, the answer is fixed. That is the point —
it can be tested anywhere, in a second, without a site.

These four moved out of fuse_manufacturing when the gateway did. They are the ones the
transport itself depends on, so they belong beside it rather than in the app that happens
to have needed it first. Everything else in that module — recipe signatures, precision
alignment, kit build order — is about stock and stayed there.
"""

import datetime
import hashlib
import xml.etree.ElementTree as ET


def control_id_for(doctype, name, purpose=""):
	"""A control ID that is the same every time for the same piece of work.

	With <uniqueid>true</uniqueid> this is what stops a retry posting a movement twice.
	"""
	raw = f"{doctype}:{name}:{purpose}".strip(":")
	return f"fuse-{hashlib.sha1(raw.encode()).hexdigest()[:16]}"


def result_keys(root):
	"""The record key from each <result>, whichever form Intacct returned it in.

	Two shapes, and only handling one of them loses the key silently:
	  create_ictransaction and friends return <result><key>123</key></result>
	  the generic <create> returns the object itself —
	    <result><data><ictransfer><RECORDNO>23</RECORDNO></ictransfer></data></result>

	Observed live: the first warehouse transfer posted successfully and came back with
	no key at all, because only <key> was being read. The posting was fine; the
	traceability was not.

	One entry per result, in order, so a caller can line keys up with the functions it
	sent. None where a result carried no key.
	"""
	if isinstance(root, str):
		root = ET.fromstring(root)

	keys = []
	for result in root.iter("result"):
		key = result.findtext(".//key")
		if key is None:
			key = result.findtext(".//RECORDNO")
		keys.append(key.strip() if key else None)
	return keys


def rejection_errors(root):
	"""Every error Intacct reported, or an empty list if it accepted the request.

	Anything that is not the word "success" is a rejection. That is deliberately a
	whitelist: the first version tested for "failure" and let `aborted` through, so a
	transaction Intacct had rolled back was recorded as a successful post. The ERPNext
	side then proceeded on the strength of it, and the two systems disagreed about stock
	that had physically moved — precisely what posting-first is supposed to prevent.

	Intacct returns HTTP 200 for business rejections, so this is the only thing standing
	between a rejected posting and a document that claims it succeeded. It is checked at
	EVERY level: control, authentication and each individual result.
	"""
	if isinstance(root, str):
		root = ET.fromstring(root)

	rejected = any(
		(status.text or "").strip().lower() not in ("", "success") for status in root.iter("status")
	)
	if not rejected:
		return []

	errors = []
	for error in root.iter("error"):
		parts = [
			(error.findtext(tag) or "").strip()
			for tag in ("errorno", "description", "description2", "correction")
		]
		joined = " | ".join(part for part in parts if part)
		if joined:
			errors.append(joined)
	return errors or ["Intacct reported a non-success status with no error detail"]


def intacct_date(value):
	"""Intacct's MM/DD/YYYY to an ISO date.

	Intacct returns US order regardless of the company's locale — this client is South
	African and reads 08/07/2026 as 7 August, while Intacct means 8 July. Parsing it the
	local way shifts a purchase order's due date by a month without failing, which is the
	worst kind of wrong: reporting still looks plausible.

	Returns None on anything unparseable rather than a guess, so a caller reports the order
	instead of inventing a date nobody chose.
	"""
	value = (value or "").strip()
	if not value:
		return None
	try:
		return datetime.datetime.strptime(value, "%m/%d/%Y").date().isoformat()
	except ValueError:
		return None
