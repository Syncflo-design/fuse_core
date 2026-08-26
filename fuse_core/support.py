"""Raising a support ticket — the one user-facing thing core owns.

Everything else in this app is plumbing: the gateway, the credentials, the switches. This
is here because support is not a Manufacturing feature or a Projects feature. A client who
bought only one of them still needs a way to ask for help, and asking for help should not
depend on which module they licensed.

The tile and the switch are contributed through the same hooks every other Fuse app uses,
so the theme needs to know nothing about it.
"""

MODULE_KEY = "support"

MODULES = [
	{
		"key": MODULE_KEY,
		"label": "Support",
		"description": (
			"Let anyone on this site raise a support ticket. It is recorded here and "
			"emailed to the support address set above. Off means the tile disappears — "
			"for a client whose own help desk handles Fuse and who does not want two "
			"routes to it."
		),
		"default": 1,
	},
]


def get_modules():
	"""This app's switches, for its own `fuse_modules` hook."""
	return [dict(module) for module in MODULES]


def get_tiles():
	"""The Support tile, for the theme's `fuse_tiles` hook.

	On the reference row rather than in the run of actions. Raising a ticket is not part of
	anybody's job — it is what you do when the job has stopped working — and it should be
	findable without competing for attention with the things people came to do.
	"""
	return [
		{
			"key": MODULE_KEY,
			"label": "Log a support ticket",
			"blurb": "Ask a question, or tell us something is wrong",
			"icon": "🛟",
			"route": ["new", "Fuse Support Ticket"],
			"group": "reference",
			# Last on the row. It is the thing you reach for when nothing else worked.
			"order": 200,
		}
	]
