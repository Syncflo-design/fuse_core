"""A question or a problem, raised with whoever supports this site.

Recorded FIRST and emailed second, never the other way round. A support request that
quietly failed to send is worse than no button at all — the person believes help is coming
and nobody knows they asked. So the ticket always exists on the site, sending is a separate
visible step, and a failure to send says so on the record instead of being swallowed.

The site details are captured rather than asked for. Asking a user which version they are
on gets a guess, and a guess is worse than nothing when it decides where support looks.

Some tickets wait for someone on the client's side to sign them off. Only the
discretionary ones — see APPROVAL_CATEGORIES. A fault never waits, because an approver on
leave must not be able to sit on a system that is down.
"""

import json

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, now_datetime

# Where tickets go when nobody has said otherwise. A partner supporting their own clients
# changes it in Intacct Settings; the code has no other opinion about who answers.
DEFAULT_SUPPORT_EMAIL = "support@syncflo.co.za"

# Who may sign one off. Held by whoever the client decides speaks for them on what is worth
# asking for — usually one or two people, not everyone who can raise a ticket.
APPROVER_ROLE = "Fuse Support Approver"

# The categories that wait, when the switch is on. Everything NOT in here goes straight
# through, and that is the important half of the rule: these are the tickets that commit
# somebody's time or money, and the rest are the ones where waiting costs more than asking.
APPROVAL_CATEGORIES = {
	"I need training",
	"We need it to work differently",
	"Nice to have",
	"New user or access",
}


class FuseSupportTicket(Document):
	def before_insert(self):
		self.raised_by = frappe.session.user
		self.raised_on = now_datetime()
		self.status = "Not sent"
		self.site_context = _context()

	def after_insert(self):
		"""Send it, or hold it for approval.

		Nobody wants a two-step support button, so a fault goes the moment it is raised.
		The record is already saved by the time this runs, so a failure here loses nothing
		— it is caught, written to the ticket and shown, rather than rolling back the
		request the user just typed out.
		"""
		if self.needs_approval():
			self.db_set("status", "Waiting for approval")
			_notify_approvers(self)
			return

		self.send()

	def needs_approval(self):
		"""Whether this one waits for somebody on the client's side.

		Three things have to be true, and the last one is the safety valve: a gate nobody
		can open is not a control, it is a ticket that vanishes. Where the role is held by
		nobody the ticket is sent anyway and says so on the record.
		"""
		if self.category not in APPROVAL_CATEGORIES:
			return False

		try:
			if not frappe.db.get_single_value("Intacct Settings", "support_needs_approval"):
				return False
		except Exception:
			# Settings not migrated yet. Not a reason to hold somebody's request.
			return False

		return bool(approvers())

	@frappe.whitelist()
	def approve(self):
		"""Sign it off and send it."""
		_only_approver()
		if self.status != "Waiting for approval":
			frappe.throw(f"{self.name} is {self.status}, so there is nothing to approve.")

		self.db_set({"approved_by": frappe.session.user, "approved_on": now_datetime()})
		return self.send()

	@frappe.whitelist()
	def decline(self, reason):
		"""Stop it, with the reason on the record.

		A reason is required. A request that came back declined with no explanation is how
		people learn to stop raising them, and then the first thing anyone hears about a
		problem is when it has become a bigger one.
		"""
		_only_approver()
		if self.status != "Waiting for approval":
			frappe.throw(f"{self.name} is {self.status}, so there is nothing to decline.")

		reason = (reason or "").strip()
		if not reason:
			frappe.throw("Say why. The person who raised it will read this.")

		self.db_set(
			{
				"status": "Declined",
				"approved_by": frappe.session.user,
				"approved_on": now_datetime(),
				"decline_reason": reason,
			}
		)
		_notify_raiser(self, reason)
		return {"declined": True}

	@frappe.whitelist()
	def send(self):
		"""Email the ticket to the support address, and record what happened."""
		address = support_email()

		try:
			frappe.sendmail(
				recipients=[address],
				# So a reply goes back to the person who raised it, not to whoever the
				# site sends mail as.
				reply_to=_user_email(self.raised_by),
				subject=f"[Fuse] {self.subject}",
				message=_body(self),
				attachments=_attachments(self),
				reference_doctype=self.doctype,
				reference_name=self.name,
				now=True,
			)
		except Exception as error:
			# Deliberately not re-raised. The commonest cause is a site with no outgoing
			# email account, which is a configuration gap rather than anything the user
			# did — and losing their typed-out problem to a traceback would be its own
			# support ticket.
			frappe.log_error(f"Fuse support ticket {self.name}", frappe.get_traceback())
			self.db_set(
				{
					"status": "Could not send",
					"sent_to": address,
					"send_error": str(error)[:900],
				}
			)
			return {"sent": False, "to": address, "error": str(error)}

		self.db_set(
			{
				"status": "Sent",
				"sent_to": address,
				"sent_on": now_datetime(),
				"send_error": None,
			}
		)
		return {"sent": True, "to": address}



@frappe.whitelist()
def approvers():
	"""Enabled users holding the approver role.

	Read every time rather than cached: the answer decides whether somebody's request is
	held, and a stale answer holds it against a role nobody has any more.
	"""
	try:
		return [
			user
			for user in frappe.get_all(
				"Has Role",
				filters={"role": APPROVER_ROLE, "parenttype": "User"},
				pluck="parent",
			)
			if frappe.db.get_value("User", user, "enabled")
		]
	except Exception:
		return []


def _only_approver():
	"""Refuse anyone who does not hold the role.

	Checked here rather than only in the form, because the form is a convenience and the
	method is the door.
	"""
	if APPROVER_ROLE in frappe.get_roles() or "System Manager" in frappe.get_roles():
		return
	frappe.throw(
		f"Only someone holding {APPROVER_ROLE} can decide on a support ticket.",
		frappe.PermissionError,
	)


def _notify_approvers(doc):
	"""Put it in front of whoever has to decide.

	A ToDo rather than only an email: it appears in their list and stays there until it is
	dealt with, which an email does not.
	"""
	for user in approvers():
		try:
			frappe.get_doc(
				{
					"doctype": "ToDo",
					"allocated_to": user,
					"reference_type": doc.doctype,
					"reference_name": doc.name,
					"description": f"Support ticket to approve: {doc.subject} ({doc.category})",
					"priority": "High" if doc.urgency == "Blocking work right now" else "Medium",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(f"Fuse support ticket {doc.name}", frappe.get_traceback())


def _notify_raiser(doc, reason):
	"""Tell the person it was declined, and why."""
	try:
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"allocated_to": doc.raised_by,
				"reference_type": doc.doctype,
				"reference_name": doc.name,
				"description": f"Support request declined: {doc.subject}. {reason}",
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(f"Fuse support ticket {doc.name}", frappe.get_traceback())

@frappe.whitelist()
def support_email():
	"""The address tickets go to on this site.

	Falls back to Syncflo rather than to nothing: a site that has never set the field still
	has to be able to ask for help, and an unconfigured support button is the one thing
	worse than no support button.
	"""
	try:
		configured = frappe.db.get_single_value("Intacct Settings", "support_email")
	except Exception:
		configured = None
	return (configured or "").strip() or DEFAULT_SUPPORT_EMAIL


def _user_email(user):
	return frappe.db.get_value("User", user, "email") or user


def _attachments(doc):
	if not doc.attachment:
		return None
	# The file the user attached, by the URL stored on the field. Passed by reference so a
	# large screenshot is not read into memory twice.
	return [{"file_url": doc.attachment}]


def _context():
	"""What support would otherwise have to ask for, gathered at the moment of asking."""
	details = {
		"site": frappe.local.site,
		"url": get_url(),
		"user": frappe.session.user,
	}

	try:
		details["company"] = frappe.defaults.get_user_default("Company")
	except Exception:
		pass

	try:
		from frappe.utils.change_log import get_versions

		details["apps"] = {
			name: info.get("version")
			for name, info in (get_versions() or {}).items()
			if name.startswith("fuse") or name in ("frappe", "erpnext")
		}
	except Exception:
		pass

	return json.dumps(details, indent=1, default=str)


def _body(doc):
	"""The email support actually reads.

	Plain sections in the order someone diagnosing works through them: what was asked, then
	what was seen, then where and who, then the machine detail last.
	"""
	rows = [
		("Subject", doc.subject),
		("Kind", doc.category),
		("Urgency", doc.urgency),
		("Raised by", f"{doc.raised_by} on {frappe.utils.format_datetime(doc.raised_on)}"),
		("Screen", doc.where_it_happened or "not recorded"),
	]

	head = "".join(
		f"<tr><td style='padding:2px 12px 2px 0;color:#666'>{label}</td>"
		f"<td style='padding:2px 0'><b>{frappe.utils.escape_html(str(value or ''))}</b></td></tr>"
		for label, value in rows
	)

	def block(title, text):
		if not text:
			return ""
		safe = frappe.utils.escape_html(text).replace("\n", "<br>")
		return f"<h4 style='margin:18px 0 4px'>{title}</h4><div>{safe}</div>"

	return (
		f"<table style='font-size:13px'>{head}</table>"
		+ block("What happened", doc.what_happened)
		+ block("What was expected", doc.what_expected)
		+ "<h4 style='margin:18px 0 4px'>Site details</h4>"
		+ f"<pre style='font-size:12px;background:#f6f8f9;padding:8px'>"
		f"{frappe.utils.escape_html(doc.site_context or '')}</pre>"
		+ f"<p style='color:#888;font-size:12px'>Fuse support ticket {doc.name}</p>"
	)
