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

# Core declares NO modules of its own. It owns the table on Intacct Settings; the features
# belong to the apps that implement them, and each contributes through this hook. That is
# what lets Manufacturing or Projects be installed and removed on their own.
#
# Deliberately empty rather than absent: an app reading frappe.get_hooks("fuse_modules")
# on a site with core alone should get a list, not a surprise.
fuse_modules = []

# Same again for the Transactions table: core owns it and the definition picker, and
# posts nothing itself. Each app declares the processes it needs mapped.
fuse_processes = []
