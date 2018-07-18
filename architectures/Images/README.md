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

To rebuild the PGDG 9.6 images for every region, run

    clusters/images/build-images -r PGDG 9.6

This will generate config.yml containing one instance per distribution
per region (see generate-config.yml), provision the cluster, deploy the
right packages, generate AMIs, and deprovision the cluster. (It won't
regenerate config.yml if you leave out the -r, but it's harmless to
leave it in.)

The resulting AMIs will be named as follows

    TPA-Debian-PGDG-9.6-20161128
    TPA-RedHat-PGDG-9.6-20161128
    TPA-Ubuntu-PGDG-9.6-20161128

To use one of these images, set ec2_ami in config.yml:

    ec2_ami:
      Name: TPA-Debian-PGDG-9.6-2016*
      Owner: self
