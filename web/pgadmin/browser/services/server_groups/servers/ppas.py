##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2016, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

from flask.ext.babel import gettext
from pgadmin.browser.services.server_groups.servers.types import ServerType


class PPAS(ServerType):
    def instanceOf(self, ver):
        return ver.startswith("EnterpriseDB")


# Default Server Type
PPAS('ppas', gettext("EDB Advanced Server"), 2)
