
.PHONY = demo all dev-setup refresh-deps migrate
build := build
node_modules := ./node_modules
env := $(build)/env
bundle := $(build)/bundle
static := $(build)/static

ifeq "$(role)" ""
role := dev
endif

django_manage := DJANGO_SETTINGS_CONFIG="tpasite.conf.$(role)" ./apps/manage.py

all:

$(build):
	mkdir -p $(build)

$(env): $(build)
	virtualenv --no-site-packages $(env)

$(static) $(bundle): $(build)
	mkdir -p $@

$(node_modules): $(build)
	mkdir -p $(node_modules) \
		&& npm install npm@latest \
		|| rmdir -f $(nodule_modules)

# Commands

dev-setup: $(env) $(node_modules) $(bundle) $(static)

refresh-deps:
	$(node_modules)/.bin/npm install
	$(env)/bin/pip install -r ./req/$(role).txt

migrate:
	$(django_manage) migrate

refresh-devserver:
	git pull
	make refresh-deps
	make migrate

refresh-instance:
	ssh -to ForwardAgent=yes tpa$(role)@tpa-$(role) -- \
		cd /home/tpa$(role)/tpa/TPA/ui \; git pull \; role=$(role) make refresh-devserver
