ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# See common-systemd/Dockerfile for an explanation.

ENV container docker
STOPSIGNAL RTMIN+3
ENV SYSTEMD_COLORS=0
COPY common-systemd/systemctl-commands.sh /root/systemctl-commands.sh
RUN bash /root/systemctl-commands.sh && rm -f /root/systemctl-commands.sh
RUN echo "NAutoVTs=0" >> /etc/systemd/logind.conf
RUN echo "ForwardToConsole=yes" >> /etc/systemd/logind.conf
CMD ["/sbin/init", "--system"]
