Images
======

In order to speed up production deployments, we can generate images with
an assortment of packages installed over the stock distribution images.

For example:

    tpaexec configure images-20180718 -a Images \
      --postgres-version 9.6

    images-20180718/build-images
