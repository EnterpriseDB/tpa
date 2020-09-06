# Copyright © 2ndQuadrant Limited <info@2ndquadrant.com>

images/bdr-simple.png: images/bdr-simple.dot
	circo -Tpng $< -o $@

images/m1.png: images/m1.dot
	dot -Tpng $< -o $@

TARGET = tpaexec.pdf

SRC = index.md INSTALL.md INSTALL-repo.md tpaexec-configure.md tpaexec-provision.md tpaexec-deploy.md tpaexec-test.md architecture-M1.md architecture-BDR-Always-ON.md architecture-BDR-Simple.md platform-aws.md platform-bare.md platform-docker.md platform-lxd.md platform-vagrant.md configure-cluster.md configure-instance.md configure-source.md tpaexec-hooks.md configure/apt_repositories.md configure/yum_repositories.md configure/tpa_2q_repositories.md configure/packages.md configure/volumes.md configure/artifacts.md configure/sysctl_values.md configure/postgres_installation_method/src.md configure/postgres_installation_method/pkg.md configure/install_from_source.md configure/git-credentials.md configure/postgres_user.md configure/initdb.md configure/pgpass.md configure/pg_hba.conf.md configure/pg_ident.conf.md configure/postgresql.conf.md configure/postgres_users.md configure/postgres_databases.md configure/pglogical.md configure/ssh_key_file.md tpaexec-rehydrate.md tpaexec-update-postgres.md tpaexec-switchover.md misc-ansible-sudo.md misc-configure-putty.md misc-troubleshooting.md

header.md: $(IMG)
	bash tools/make-header.sh >$@

tpaexec.md: header.md $(SRC)
	sed -e '$$s/$$/\n/' -e 's/—/\\textemdash{}/g' -e 's/©/\\copyright/g' -e 's/…/\\dots/g' -s $^ >$@

$(TARGET): tpaexec.md
	2ndq-pandoc tpaexec.md --filter=tools/single-pdf.py --listings

clean:
	rm -rf header.md tpaexec.md $(TARGET)

all: $(TARGET)

.PHONY: all $(SUBDIRS)
