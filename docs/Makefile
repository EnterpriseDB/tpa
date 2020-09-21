# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

images/bdr-simple.png: images/bdr-simple.dot
	circo -Tpng $< -o $@

images/m1.png: images/m1.dot
	dot -Tpng $< -o $@

TARGET = tpaexec.pdf

SRC = index.md INSTALL.md INSTALL-repo.md tpaexec-configure.md tpaexec-provision.md tpaexec-deploy.md tpaexec-test.md architecture-M1.md architecture-BDR-Always-ON.md architecture-BDR-Simple.md platform-aws.md platform-bare.md platform-docker.md platform-lxd.md platform-vagrant.md configure-cluster.md configure-instance.md configure-source.md tpaexec-hooks.md distributions.md python.md apt_repositories.md yum_repositories.md tpa_2q_repositories.md packages.md volumes.md artifacts.md sysctl_values.md hosts.md postgres_installation_method_pkg.md postgres_installation_method_src.md install_from_source.md git-credentials.md postgres_user.md initdb.md pgpass.md pg_hba.conf.md pg_ident.conf.md postgresql.conf.md postgres_users.md postgres_databases.md pglogical.md ssh_key_file.md tpaexec-rehydrate.md tpaexec-update-postgres.md tpaexec-switchover.md misc-ansible-sudo.md misc-configure-putty.md misc-troubleshooting.md

header.md: $(IMG) tools/make-header.sh
	bash tools/make-header.sh >$@

tpaexec.md: header.md $(SRC)
	sed -e '$$s/$$/\n/' -e 's/—/\\textemdash{}/g' -e 's/©/\\copyright/g' -e 's/…/\\dots/g' -s $^ >$@

$(TARGET): tpaexec.md
	2ndq-pandoc tpaexec.md --filter=tools/single-pdf.py --listings

clean:
	rm -rf header.md tpaexec.md $(TARGET)

all: $(TARGET)

.PHONY: all $(SUBDIRS)
