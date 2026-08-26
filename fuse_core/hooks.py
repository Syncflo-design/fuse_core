app_name        = "fuse_core"
app_title       = "Fuse Core"
app_publisher   = "Syncflo"
app_description = "Sage Intacct connection for Fuse — gateway, credentials, module switches and the request log."
app_email       = "ops@syncflo.co.za"
app_license     = "MIT"

# Both, because after_migrate has been seen not to fire on a Frappe Cloud deploy — the
# code ships and the configuration that goes with it does not. Also callable as
# fuse_core.api.setup for the same reason. Everything it does is idempotent.
after_install = "fuse_core.install.after_install"
after_migrate = "fuse_core.install.after_install"

# Core owns the table on Intacct Settings and almost no features: they belong to the apps
# that implement them, and each contributes through this hook. That is what lets
# Manufacturing or Projects be installed and removed on their own.
#
# The one exception is Support. A client who licensed only one module still needs a way to
# ask for help, so raising a ticket cannot live in a module they might not have.
fuse_modules = ["fuse_core.support.get_modules"]

# The Support tile, for the same reason. Core ships no other user-facing screen.
fuse_tiles = ["fuse_core.support.get_tiles"]

# And the guide that goes with it.
fuse_guides = ["fuse_core.guides.get_guides"]

# Same again for the Transactions table: core owns it and the definition picker, and
# posts nothing itself. Each app declares the processes it needs mapped.
fuse_processes = []
