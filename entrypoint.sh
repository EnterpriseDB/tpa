#!/usr/bin/env bash
# © Copyright EnterpriseDB UK Limited 2015-2023 - All rights reserved.

# We should be in workdir
/usr/local/bin/tpaexec "$@"
res=$?
[ -n "$USER_ID" ] && chown "$USER_ID" -R .
[ -n "$GROUP_ID" ] && chgrp "$GROUP_ID" -R .
exit "$res"
