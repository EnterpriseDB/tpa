ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV container docker
#
# This image won't shutdown on SIGTERM. It expects the custom stop signal
# RTMIN+3 per systemd requirements. TPAexec will set this automatically and
# 'docker stop' knows to use it. But declare it in the image itself to be
# extra clear.
#
# Systemd won't respond to SIGINT either, so control-C won't stop it if
# you launch it interactively.
#
STOPSIGNAL RTMIN+3
#
# Run a minimal systemd only, don't try to bring up a full system.
#
ENV SYSTEMD_COLORS=0
COPY systemctl-commands.sh /root/systemctl-commands.sh
RUN bash /root/systemctl-commands.sh && rm -f /root/systemctl-commands.sh
RUN echo "NAutoVTs=0" >> /etc/systemd/logind.conf

#
# Run systemd.
#
# This container should run unprivileged i.e. with no --privileged flag.
# It expects the presence of oci-systemd-hook in the Docker host. See
# https://github.com/projectatomic/oci-systemd-hook and
# https://developers.redhat.com/blog/2016/09/13/running-systemd-in-a-non-privileged-container/
#
# Unfortunately Docker CE does not support running OCI hooks. runc does and so
# does the patched Docker on RHEL and Fedora. For regular Docker CE you need to
# do some extra steps, e.g.:
#
#     docker run -ti --tmpfs /tmp --tmpfs /run -v /sys/fs/cgroup:/sys/fs/cgroup:ro local/centos7-systemd
#
# Note: If you are on an OCI hooks enabled build but want to suppress the
# oci-systemd-hook that automounts /tmp etc, add:
#
#     --env oci-systemd-hook=disabled
#
# Handy hints for observing the container:
#
# List units
#
#    docker exec -it $CONTAINERID systemctl -a -l --no-pager
#
# List processes
#
#    docker exec -it ps aux
#
# Observe container start/stop etc: run "docker events" in another terminal.
#
# See https://www.freedesktop.org/software/systemd/man/systemd.html for systemd env vars etc.
#
# If you want more info on systemd startup you can add --show-status to the command line.
#
CMD ["/sbin/init", "--system"]
