TPA Images
----------

TPA can set up stock Debian/RedHat/Ubuntu instances with everything they
need, but in practice it's not viable for production deployments because
the time it takes to install packages is both too long and too variable.
So we create custom AMIs that comprise the base images and the packages
that deploy.yml might end up installing.

(In theory, we're not limited to installing packages when building AMIs.
Any task that doesn't depend on the node's identity, such as configuring
logrotate, is acceptable. Installing packages is just the obvious thing
to start with. We can always move more tasks to the image stage as the
fancy strikes us; and if we miss some, well, deploy.yml will take care
of it later, because it's carefully written to be idempotent.)
