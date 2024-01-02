#!/usr/bin/env bash
# © Copyright EnterpriseDB UK Limited 2015-2024 - All rights reserved.

reset_perms() {
    [ -n "$USER_ID" ] && chown "$USER_ID" -R /work
    [ -n "$GROUP_ID" ] && chgrp "$GROUP_ID" -R /work
}
# Ensure the reset is ran if the container is stopped with `docker stop` or `docker kill`
trap 'reset_perms' SIGTERM

/usr/local/bin/tpaexec "$@" &
wait $!
# SIGINT whilst child proc is running is not seen by trap so we run a copy here instead of using
# trap copy_output SIGINT EXIT
reset_perms
