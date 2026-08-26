// Fuse Support Ticket — the desk form.
//
// The one thing this adds over the plain form: it records WHERE the user was when they
// clicked the tile. A ticket that says "it broke" is a conversation; a ticket that says
// "it broke on Warehouse Transfer" is a diagnosis, and nobody remembers to type it.

const METHODS = "fuse_core.fuse_core.doctype.fuse_support_ticket.fuse_support_ticket";

frappe.ui.form.on("Fuse Support Ticket", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.where_it_happened) {
			frm.set_value("where_it_happened", previous_screen());
		}
	},

	refresh(frm) {
		render_banner(frm);

		if (frm.is_new()) {
			return;
		}

		if (frm.doc.status === "Waiting for approval") {
			approval_buttons(frm);
			frm.dashboard.set_headline(
				__("Waiting for someone to approve it. Nothing has been sent yet.")
			);
			return;
		}

		if (frm.doc.status === "Declined") {
			frm.dashboard.set_headline(
				__("Declined by {0}. It was not sent.", [frm.doc.approved_by])
			);
			return;
		}

		// Sending happens by itself when the ticket is raised. This is for the case where
		// it could not go — a site with no outgoing email, a mail server that was down —
		// so somebody can try again once that is fixed, without retyping anything.
		if (frm.doc.status !== "Sent") {
			frm.add_custom_button(__("Send to support"), () => {
				frm.call("send").then(({ message }) => {
					if (message && message.sent) {
						frappe.show_alert({
							message: __("Sent to {0}", [message.to]),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("It did not send"),
							indicator: "red",
							message: __(
								"The ticket is saved here, so nothing you typed is lost. {0}",
								[(message && message.error) || ""]
							),
						});
					}
					frm.reload_doc();
				});
			});
		}

		if (frm.doc.status === "Sent") {
			frm.dashboard.set_headline(
				__("Sent to {0}. A reply will come back to your email address.", [frm.doc.sent_to])
			);
		}
	},
});

function approval_buttons(frm) {
	// Only shown to somebody who can actually use them. The server checks the role again
	// when either is clicked — this is the convenience, that is the door.
	const roles = frappe.user_roles || [];
	if (!roles.includes("Fuse Support Approver") && !roles.includes("System Manager")) {
		return;
	}

	frm.add_custom_button(__("Approve and send"), () => {
		frm.call("approve").then(({ message }) => {
			if (message && message.sent) {
				frappe.show_alert({ message: __("Sent to {0}", [message.to]), indicator: "green" });
			} else {
				frappe.msgprint({
					title: __("Approved, but it did not send"),
					indicator: "orange",
					message: __("The ticket is saved. {0}", [(message && message.error) || ""]),
				});
			}
			frm.reload_doc();
		});
	}).addClass("btn-primary");

	frm.add_custom_button(__("Decline"), () => {
		frappe.prompt(
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Why"),
				reqd: 1,
				// Said plainly, because it is read by the person whose request this was.
				description: __("The person who raised it will read this."),
			},
			({ reason }) => {
				frm.call("decline", { reason }).then(() => frm.reload_doc());
			},
			__("Decline this request"),
			__("Decline")
		);
	});
}

function previous_screen() {
	// The route the user came from, not this one. frappe.route_history holds the trail and
	// its last entry is the form we are standing on.
	const history = frappe.route_history || [];
	const previous = history[history.length - 2];
	if (!previous || !previous.length) {
		return "";
	}
	return previous.join(" / ");
}

function render_banner(frm) {
	const wrapper = frm.fields_dict.detail_section?.$wrapper;
	if (!wrapper) {
		return;
	}

	frm.$fuse_banner?.remove();
	if (!frm.is_new()) {
		return;
	}

	// Styled inline rather than from a stylesheet — one element, and a bundled stylesheet
	// has to be cache-busted on every change.
	frm.$fuse_banner = $(`
		<div style="
			border-left: 3px solid var(--primary, #2490ef);
			background: var(--fg-color, #fff);
			padding: 10px 14px;
			margin: 0 0 14px 0;
			border-radius: var(--border-radius-md, 6px);
			box-shadow: var(--card-shadow, none);
		">
			<div style="font-weight: 600; color: var(--text-color); margin-bottom: 2px;">
				${__("Tell us what happened")}
			</div>
			<div style="color: var(--text-muted); font-size: var(--text-sm, 12px);">
				${__("Saving sends this to support. Your site details and the screen you came from are attached automatically, so there is no need to describe them.")}
			</div>
		</div>
	`).insertBefore(wrapper);
}
