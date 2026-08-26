"""The user guides this app ships.

Core ships one, for the one user-facing thing it owns: raising a support ticket. It lives
here rather than in Manufacturing for the same reason the tile does — a client who
licensed only Projects still needs to know how to ask for help.

The theme merges what every Fuse app contributes through the `fuse_guides` hook, so this
appears on the Training page alongside the rest without either app knowing about the other.

WRITTEN in `docs/training/*.md`, SERVED from `public/files/training/*.html`. The build tool
lives in the Manufacturing repo, because one build tool for every app beats a copy per repo
drifting apart:

    python <fuse_manufacturing>/fuse_manufacturing/docs/build_guides.py C:/ClaudeCode/fuse_core/fuse_core

The HTML is generated. A hand edit to it is lost on the next build.
"""

# Path is relative to /assets/fuse_core/files/.
GUIDES = [
	{"title": "Logging a Support Ticket", "file": "training/01 Logging a Support Ticket.html"},
	# Written for a different reader: the one or two people on the client's side who decide
	# whether a request is raised at all, not the person raising it.
	{
		"title": "Approving Support Tickets",
		"file": "training/02 Approving Support Tickets.html",
	},
]


def get_guides():
	"""This app's guides, for the theme's `fuse_guides` hook.

	Copies, not the list itself: the theme merges what every app contributes, and a caller
	that edited the result would be editing this module's own registry.
	"""
	return [
		{
			"title": guide["title"],
			"url": f"/assets/fuse_core/files/{guide['file']}",
			"is_pdf": guide["file"].lower().endswith(".pdf"),
		}
		for guide in GUIDES
	]
