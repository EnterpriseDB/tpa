Images
======

In order to speed up production deployments, we can generate images with
an assortment of packages installed over the stock distribution images.

For example:

    tpaexec configure images-20180718 -a Images \
      --regions eu-west-1 eu-west-2 eu-west-3 us-east-1 \
      --distributions Debian RedHat Ubuntu \
      --image-name 'TPA-{distribution}-{label}-{version}-{date}' \
      --image-label 'Postgres' --image-version '9.6' \
      --postgres-version 9.6

    tpaexec build-images images-20180718 -v
