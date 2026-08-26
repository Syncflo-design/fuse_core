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


# Lucide "life-buoy", as SVG path elements. The bottom row draws its cards with a stroked
# icon that takes its colour from the stylesheet, which an emoji cannot do — and next to two
# cards that already do, an emoji is the one that looks wrong.
ICON_SVG = (
	'<circle cx="12" cy="12" r="10"></circle>'
	'<circle cx="12" cy="12" r="4"></circle>'
	'<path d="m4.93 4.93 4.24 4.24"></path>'
	'<path d="m14.83 9.17 4.24-4.24"></path>'
	'<path d="m14.83 14.83 4.24 4.24"></path>'
	'<path d="m9.17 14.83-4.24 4.24"></path>'
)


def get_tiles():
	"""The Support tile, for the theme's `fuse_tiles` hook.

	On the bottom row, beside the shop floor link and the guides, rather than among the
	modules. That row is for the things that are not part of anybody's job — help, and how
	to ask for help — and raising a ticket is what you do when the job has stopped working.
	"""
	return [
		{
			"key": MODULE_KEY,
			"label": "Log a support ticket",
			"blurb": "Ask a question, or tell us something is wrong",
			"icon": "🛟",
			"svg": ICON_SVG,
			"route": ["new", "Fuse Support Ticket"],
			"group": "footer",
			# After the guides. Look it up first, then ask.
			"order": 10,
		}
	]
