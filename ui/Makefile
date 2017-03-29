
.PHONY = demo all dev-setup refresh-deps migrate
build := ./build
node_modules := ./node_modules
env := $(build)/env
bundle := $(build)/bundle
static := $(build)/static

ifeq "$(role)" ""
role := dev
endif

ifneq "$(VIRTUAL_ENV)" ""
env := "$(VIRTUAL_ENV)"
endif

npm := $(node_modules)/.bin/npm
webpack := $(node_modules)/.bin/webpack
pip := $(env)/bin/pip
django_manage := DJANGO_SETTINGS_CONFIG="tpasite.conf.$(role)" ./apps/manage.py

all:

$(build):
	mkdir -p $(build)

$(env): $(build)
	test -d $(env) || virtualenv --no-site-packages $(env) && $(pip) install --upgrade pip

$(static) $(bundle): $(build)
	mkdir -p $@

$(node_modules): $(build)
	mkdir -p $(node_modules)

$(npm): $(node_modules)
	test -x $(npm) || npm install npm@latest

$(webpack): $(npm)
	$(npm) install

$(pip): $(env)

# Commands

dev-setup: $(pip) $(webpack) $(bundle) $(static)

refresh-deps: $(npm) $(pip)
	$(node_modules)/.bin/npm install
	$(env)/bin/pip install -r ./req/$(role).txt

migrate:
	$(django_manage) migrate

refresh-devserver: refresh-deps migrate

refresh-instance:
	ssh -to ForwardAgent=yes tpa$(role)@tpa-$(role) -- \
		cd /home/tpa$(role)/tpa/TPA/ui \; git pull \; role=$(role) make refresh-devserver
