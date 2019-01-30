# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

images/bdr-simple.png: images/bdr-simple.dot
	circo -Tpng $< -o $@

images/m1.png: images/m1.dot
	dot -Tpng $< -o $@

TARGET = tpaexec.pdf

SRC = index.md INSTALL.md INSTALL-repo.md tpaexec-configure.md tpaexec-provision.md tpaexec-deploy.md tpaexec-test.md architecture-M1.md architecture-CAMO2x2.md architecture-BDR-Always-ON.md architecture-BDR-Simple.md platform-aws.md platform-bare.md platform-docker.md platform-lxd.md platform-vagrant.md configure-cluster.md configure-instance.md tpaexec-rehydrate.md tpaexec-switchover.md misc-configure-putty.md misc-troubleshooting.md

$(TARGET): cache/header.md $(SRC)
	sed -e '$$s/$$/\n/' -e 's/—/\\textemdash{}/g' -e 's/©/\\copyright/g' -e 's/…/\\dots/g' -s $^ > cache/tpaexec.md
	2ndq-pandoc cache/tpaexec.md --filter=tools/single-pdf.py --listings
	cp cache/tpaexec.pdf $@

cache/header.md: $(IMG)
	bash tools/make-header.sh >$@

clean:
	rm -f cache/* $(TARGET)

all: $(TARGET)

.PHONY: all $(SUBDIRS)
