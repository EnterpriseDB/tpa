# Makefile to assist with common tasks that would be executed by a developer
#
# Goal is to have `all` as
# all: prep lint test document
#
# Other commands implemented and possible future commands to extend:
# make  # create a venv, run lint, test, build, document generation/test
# make <verb>  # Ran one of lint, test, clean, tag, etc.
# make update  # git pull, merge changes from template, updated hooks
# make tag  # bumped version for release, created git tag, pushed
# make minor/major/patch  # like above for semver versioning

WORKON_HOME ?= ~/.virtualenvs
NAME = $(shell basename $(PWD))
OPEN = $(shell command -v open || command -v xdg-open)

ifdef DEB_BUILD_ARCH
all:
else
all: prep dep_test test document
endif
.PHONY: all prep update

# Note venv will not interfere with tpaexec tpa-venv if created so we can be clean in these operations
venv:
	mkdir -p $(WORKON_HOME)
	python3.6 -m venv $(WORKON_HOME)/$(NAME)

install_requirements: venv
	$(WORKON_HOME)/$(NAME)/bin/pip install -r requirements.txt -r requirements/ansible.txt

tox: venv
	$(WORKON_HOME)/$(NAME)/bin/pip install tox

lint: tox
	$(WORKON_HOME)/$(NAME)/bin/tox -e py36-lint

ifdef DEB_BUILD_ARCH
test:
else
test: tox
	$(WORKON_HOME)/$(NAME)/bin/tox -e py36-test
	$(OPEN) test-output/tests.html
	sleep 1
	$(OPEN) test-output/coverage/index.html
endif

dep_test: tox
	$(WORKON_HOME)/$(NAME)/bin/tox -e dep

integ_test:
	act -W .github/workflows/simple_integration_tests.yml workflow_dispatch

document: venv
	$(WORKON_HOME)/$(NAME)/bin/pip install -r requirements/document.txt
	. $(WORKON_HOME)/$(NAME)/bin/activate && $(MAKE) -C docs all
	$(OPEN) docs/pdf/tpaexec.pdf

pull:
	git pull

update: pull install_requirements

install_update_reqs: venv
	$(WORKON_HOME)/$(NAME)/bin/pip install pip-tools

%.txt: %.in
	pip-compile --generate-hashes -o $@ $<

REQUIREMENTS_IN = $(wildcard *.in requirements/*in)
REQUIREMENTS_TXT = $(REQUIREMENTS_IN:.in=.txt)
.PHONY: $(REQUIREMENTS_IN)
update_reqs: install_update_reqs $(REQUIREMENTS_TXT)

black:
	$(WORKON_HOME)/$(NAME)/bin/pip install black
	$(WORKON_HOME)/$(NAME)/bin/black lib library

prep: update_reqs black

ifdef DEB_BUILD_ARCH
clean:
else
clean:
	rm -rf $(WORKON_HOME)/$(NAME) .tox .pytest_cache .coverage \
	test-output coverage-reports workflow docs/pdf/*.pdf ansible.log
	find . -name \*.pyc -delete
	find . -depth -name __pycache__ -delete
endif
